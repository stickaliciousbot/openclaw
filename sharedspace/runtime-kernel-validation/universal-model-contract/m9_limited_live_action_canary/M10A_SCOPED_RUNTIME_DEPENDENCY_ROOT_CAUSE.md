# M10A Scoped Runtime Dependency Root Cause

Status: `PASS_M10A_SCOPED_RUNTIME_DEPENDENCY_ROOT_CAUSE_CLASSIFIED`

Classification: `SCOPED_OVERLAY_OMITTED_GENERATED_RUNTIME_DEPENDENCY_CHUNK`

The previous scoped overlay preserved M8 but copied only the M10A entry file. The built M10A entry imports generated support chunks through the M8/M7/M6 chain, so the overlay must include the full runtime dependency closure while still excluding preserved M2-M9 entry artifacts such as the canonical M8 entry file.
