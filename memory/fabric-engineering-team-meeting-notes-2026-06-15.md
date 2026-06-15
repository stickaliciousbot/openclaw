# Fabric Engineering Team Meeting Notes — DigitalTwinBuilderFlow ExecuteOperations

Date: 2026-06-15

## DigitalTwinBuilderFlow public execution gap

We can create and export `DigitalTwinBuilderFlow` items through the public Fabric REST API, including a dedicated flow with a valid `OperationId`. However, attempting to execute the flow through the documented Fabric Job Scheduler endpoint fails with HTTP 400 `InvalidJobType`.

Tested endpoint:

```text
POST /v1/workspaces/{workspaceId}/items/{digitalTwinBuilderFlowId}/jobs/ExecuteOperations/instances
```

Observed failures:

- On-demand flow: HTTP 400 `InvalidJobType`, requestId `a73eb06a-d0e2-4424-8bdd-04a81d892209`
- Dedicated flow with explicit valid operation ID: HTTP 400 `InvalidJobType`, requestId `38c83098-15e2-4feb-9da6-ceb4e826574e`

The documentation states `DigitalTwinBuilderFlow` jobs appear as `ExecuteOperations` in item job event logs, and DTB flow documentation states flows execute mapping and contextualization operations. Please confirm whether `ExecuteOperations` is publicly invokable through the Job Scheduler API for `DigitalTwinBuilderFlow`, or whether DTB flow execution is currently UI/scheduler-only.

## Evidence from Douglas Bagmaker test

- Fresh corrected DTB: `DouglasBagmakerDTB_NodeDemo_ParentFirst_NoSchema_20260615_1556`
- DTB ID: `a15b7aa0-e65b-4a75-9d01-08429b271d8d`
- On-demand flow ID: `b2fcdefb-94c7-4445-9bd0-3f6289963bea`
- Dedicated explicit-operation flow: `Run_Equipment_equipment_API_20260615_1609`
- Dedicated flow ID: `0458f74e-f125-41d5-a70b-ccedea04963c`
- Operation ID tested: `78bd6721-8881-57b0-8fce-d48be0c0fe8e` (`Equipment_equipment`)

Conclusion: DTB Flow creation/export is publicly exposed. DTB Flow execution appears to be UI/scheduler/internal only, not currently callable through the public Fabric Job Scheduler API in this tenant/item state.
