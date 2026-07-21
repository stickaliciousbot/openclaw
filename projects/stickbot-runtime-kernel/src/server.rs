use crate::kernel::KernelState;
use crate::types::{PromotionEvaluateRequest, WorkerHeartbeat, WorkerHeartbeatAck};
use anyhow::Result;
use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::response::sse::{Event, KeepAlive, Sse};
use axum::routing::{get, post};
use axum::{Json, Router};
use futures_util::Stream;
use std::convert::Infallible;
use std::net::SocketAddr;
use tokio_stream::wrappers::BroadcastStream;
use tokio_stream::StreamExt;

pub fn router(state: KernelState) -> Router {
    Router::new()
        .route("/v1/health", get(get_health))
        .route("/v1/services", get(get_services))
        .route("/v1/services/:service_id/heartbeat", post(post_heartbeat))
        .route("/v1/events/stream", get(event_stream))
        .route("/v1/promotion-gates", get(get_promotion_gates))
        .route("/v1/promotion-gates/:provider/:lane", get(get_promotion_gate_two))
        .route("/v1/promotion-gates/:provider/:lane/evaluate", post(post_promotion_gate_evaluate_two))
        .route("/v1/promotion-gates/:provider/:lane/assert", post(post_promotion_gate_assert_two))
        .route("/v1/promotion-gates/:lane_id", get(get_promotion_gate_one))
        .route("/v1/promotion-gates/:lane_id/evaluate", post(post_promotion_gate_evaluate_one))
        .route("/v1/promotion-gates/:lane_id/assert", post(post_promotion_gate_assert_one))
        .route("/v1/promotion-gates/:lane_id/assert", get(get_promotion_gate_assert_one))
        .with_state(state)
}

async fn get_health(State(state): State<KernelState>) -> Json<crate::types::KernelHealth> {
    Json(state.health().await)
}

async fn get_services(State(state): State<KernelState>) -> Json<Vec<crate::types::ServiceStatus>> {
    Json(state.services().await)
}

async fn post_heartbeat(
    State(state): State<KernelState>,
    Path(service_id): Path<String>,
    Json(heartbeat): Json<WorkerHeartbeat>,
) -> Json<WorkerHeartbeatAck> {
    Json(state.accept_worker_heartbeat(&service_id, heartbeat).await)
}

async fn get_promotion_gates() -> Json<crate::types::PromotionGateListResponse> {
    Json(crate::promotion::list_promotion_gates())
}

async fn get_promotion_gate_one(Path(lane_id): Path<String>) -> Result<Json<crate::types::PromotionEligibilityRecord>, StatusCode> {
    crate::promotion::latest_record_for_lane(&lane_id).map(Json).ok_or(StatusCode::NOT_FOUND)
}

async fn get_promotion_gate_two(Path((provider, lane)): Path<(String, String)>) -> Result<Json<crate::types::PromotionEligibilityRecord>, StatusCode> {
    let lane_id = format!("{}/{}", provider, lane);
    crate::promotion::latest_record_for_lane(&lane_id).map(Json).ok_or(StatusCode::NOT_FOUND)
}

async fn post_promotion_gate_evaluate_one(
    State(state): State<KernelState>,
    Path(lane_id): Path<String>,
    Json(req): Json<PromotionEvaluateRequest>,
) -> Result<Json<crate::types::PromotionEligibilityRecord>, (StatusCode, String)> {
    state.poll_once().await.map_err(internal_error)?;
    crate::promotion::evaluate_promotion_gate(&state, &lane_id, req).await.map(Json).map_err(internal_error)
}

async fn post_promotion_gate_evaluate_two(
    State(state): State<KernelState>,
    Path((provider, lane)): Path<(String, String)>,
    Json(req): Json<PromotionEvaluateRequest>,
) -> Result<Json<crate::types::PromotionEligibilityRecord>, (StatusCode, String)> {
    let lane_id = format!("{}/{}", provider, lane);
    state.poll_once().await.map_err(internal_error)?;
    crate::promotion::evaluate_promotion_gate(&state, &lane_id, req).await.map(Json).map_err(internal_error)
}

async fn post_promotion_gate_assert_one(Path(lane_id): Path<String>) -> Result<Json<crate::types::PromotionGateAssertResponse>, (StatusCode, Json<crate::types::PromotionGateAssertResponse>)> {
    promotion_assert_response(lane_id)
}

async fn get_promotion_gate_assert_one(Path(lane_id): Path<String>) -> Result<Json<crate::types::PromotionGateAssertResponse>, (StatusCode, Json<crate::types::PromotionGateAssertResponse>)> {
    promotion_assert_response(lane_id)
}

async fn post_promotion_gate_assert_two(Path((provider, lane)): Path<(String, String)>) -> Result<Json<crate::types::PromotionGateAssertResponse>, (StatusCode, Json<crate::types::PromotionGateAssertResponse>)> {
    promotion_assert_response(format!("{}/{}", provider, lane))
}

fn promotion_assert_response(lane_id: String) -> Result<Json<crate::types::PromotionGateAssertResponse>, (StatusCode, Json<crate::types::PromotionGateAssertResponse>)> {
    let response = crate::promotion::assert_promotion_allowed(crate::promotion::latest_record_for_lane(&lane_id), &lane_id);
    if response.allowed { Ok(Json(response)) } else { Err((StatusCode::CONFLICT, Json(response))) }
}

fn internal_error(e: anyhow::Error) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, e.to_string())
}

async fn event_stream(State(state): State<KernelState>) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let rx = state.subscribe();
    let stream = BroadcastStream::new(rx).filter_map(|item| match item {
        Ok(event) => {
            let data = serde_json::to_string(&event).unwrap_or_else(|_| "{}".to_string());
            Some(Ok(Event::default().id(event.seq.to_string()).event(event.event_type).data(data)))
        }
        Err(_) => None,
    });
    Sse::new(stream).keep_alive(KeepAlive::default())
}

pub async fn serve(state: KernelState, bind: SocketAddr) -> Result<()> {
    let app = router(state.clone());
    let listener = tokio::net::TcpListener::bind(bind).await?;
    let runtime_url = format!("http://{}", listener.local_addr()?);
    state.spawn_supervised_fixture_workers(runtime_url);
    axum::serve(listener, app).await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::journal::EventJournal;
    use crate::kernel::KernelState;
    use crate::projection::ProjectionWriter;
    use crate::registry::load_registry;
    use crate::types::{NewRuntimeEvent, Severity};
    use serde_json::json;

    #[tokio::test]
    async fn sse_order_source_is_broadcast_journal_sequence() {
        let dir = tempfile::tempdir().unwrap();
        let registry_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("config/registry.yaml");
        let mut registry = load_registry(registry_path).unwrap();
        registry.kernel.state_dir = dir.path().join("state").display().to_string();
        let journal = EventJournal::open(dir.path().join("events.sqlite")).unwrap();
        let projections = ProjectionWriter::new(dir.path().join("state"));
        let state = KernelState::new(registry, journal, projections).await.unwrap();
        let mut rx = state.subscribe();
        let e1 = state.append_event(NewRuntimeEvent { source: "test".into(), event_type: "ordered.one".into(), service_id: None, correlation_id: None, severity: Severity::Info, payload: json!({}), dedupe_key: None, schema_version: 1 }).await.unwrap();
        let e2 = state.append_event(NewRuntimeEvent { source: "test".into(), event_type: "ordered.two".into(), service_id: None, correlation_id: None, severity: Severity::Info, payload: json!({}), dedupe_key: None, schema_version: 1 }).await.unwrap();
        let r1 = rx.recv().await.unwrap();
        let r2 = rx.recv().await.unwrap();
        assert_eq!(r1.seq, e1.seq);
        assert_eq!(r2.seq, e2.seq);
        assert!(r2.seq > r1.seq);
    }
}
