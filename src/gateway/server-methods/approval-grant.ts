import {
  ApprovalGrantBroker,
  buildExecutionBoundary,
  buildChannelNeutralPresentationBinding,
  validateApprovalGrantEnvelope,
  type ApprovalGrantDecision,
  type ApprovalGrantEnvelope,
  type ApprovalGrantExecutionBoundary,
} from "../approval-grant-broker.js";
import { ErrorCodes, errorShape } from "../protocol/index.js";
import type { GatewayRequestHandlers } from "./types.js";

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isDecision(value: unknown): value is ApprovalGrantDecision {
  return value === "allow-once" || value === "deny";
}

function isBoundary(value: unknown): value is ApprovalGrantExecutionBoundary {
  return (
    isObject(value) &&
    typeof value.method === "string" &&
    typeof value.approvalId === "string" &&
    typeof value.commandSha256 === "string" &&
    typeof value.requestPayloadSha256 === "string"
  );
}

export function createApprovalGrantHandlers(broker: ApprovalGrantBroker): GatewayRequestHandlers {
  return {
    "approval.grant.issue": async ({ params, respond }) => {
      if (!isObject(params)) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "params object required"));
        return;
      }
      const decision = params.decision;
      if (typeof params.approvalId !== "string" || !isDecision(decision)) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "approvalId and decision are required"));
        return;
      }
      const boundary = isBoundary(params.executionBoundary)
        ? params.executionBoundary
        : buildExecutionBoundary({
            method: "approval.grant.consume",
            approvalId: params.approvalId,
            host: params.host === "node" ? "node" : "gateway",
            command: typeof params.command === "string" ? params.command : "",
            commandArgv: Array.isArray(params.commandArgv) ? params.commandArgv.map(String) : null,
            cwd: typeof params.cwd === "string" ? params.cwd : null,
            nodeId: typeof params.nodeId === "string" ? params.nodeId : null,
            agentId: typeof params.agentId === "string" ? params.agentId : null,
            sessionKey: typeof params.sessionKey === "string" ? params.sessionKey : null,
            requestPayload: params.requestPayload ?? params,
          });
      const presentationBinding = isObject(params.presentationBinding)
        ? (params.presentationBinding as Parameters<typeof broker.issue>[0]["presentationBinding"])
        : buildChannelNeutralPresentationBinding({
            promptText: typeof params.promptText === "string" ? params.promptText : params.approvalId,
            routeDescriptor: typeof params.routeDescriptor === "string" ? params.routeDescriptor : null,
          });
      const result = broker.issue({
        approvalId: params.approvalId,
        decision,
        executionBoundary: boundary,
        presentationBinding,
        ttlMs: typeof params.ttlMs === "number" ? params.ttlMs : 60_000,
        preRegisteredApprovalIds: new Set([params.approvalId]),
        rawChannelMetadata: params.rawChannelMetadata,
        environmentApprovalClaim: params.environmentApprovalClaim,
      });
      if (!result.ok) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, result.code, { details: result.receipt }));
        return;
      }
      respond(true, { grant: result.grant, receipt: result.receipt }, undefined);
    },
    "approval.grant.consume": async ({ params, respond }) => {
      if (!isObject(params) || !validateApprovalGrantEnvelope(params.grant)) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "valid grant envelope required"));
        return;
      }
      const grant = params.grant as ApprovalGrantEnvelope;
      if (!isBoundary(params.executionBoundary)) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, "executionBoundary is required"));
        return;
      }
      const result = broker.consume({ grant, executionBoundary: params.executionBoundary });
      if (!result.ok) {
        respond(false, undefined, errorShape(ErrorCodes.INVALID_REQUEST, result.code, { details: result.receipt }));
        return;
      }
      respond(true, { ok: true, receipt: result.receipt }, undefined);
    },
    "approval.grant.observe": async ({ respond }) => {
      respond(true, { rows: broker.rowsForObserver() }, undefined);
    },
  };
}
