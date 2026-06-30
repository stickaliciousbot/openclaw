export const GE2_MILESTONES = Object.freeze({
  ACCEPTED: 'accepted',
  VALIDATED: 'validated',
  RUNNING: 'running',
  MILESTONE_EMITTED: 'milestone_emitted',
  ARTIFACT_WRITTEN: 'artifact_written',
  VERIFICATION_PASSED: 'verification_passed',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
});

export const GE2_RUN_STATUSES = Object.freeze([
  GE2_MILESTONES.ACCEPTED,
  GE2_MILESTONES.VALIDATED,
  GE2_MILESTONES.RUNNING,
  GE2_MILESTONES.MILESTONE_EMITTED,
  GE2_MILESTONES.ARTIFACT_WRITTEN,
  GE2_MILESTONES.VERIFICATION_PASSED,
  GE2_MILESTONES.COMPLETED,
  GE2_MILESTONES.FAILED,
  GE2_MILESTONES.CANCELLED
]);

const VALID = new Set(Object.values(GE2_MILESTONES));

export function isValidMilestone(name) {
  return VALID.has(name);
}

export function createMilestone(name, detail = null, metadata = null) {
  if (!isValidMilestone(name)) {
    throw new Error(`Invalid GE2 milestone: ${String(name)}`);
  }

  return {
    milestone: name,
    detail,
    metadata,
    at: new Date().toISOString()
  };
}
