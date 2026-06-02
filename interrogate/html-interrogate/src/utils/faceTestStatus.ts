export type FaceTestStatus = 0 | 1 | 2
export type FaceBaselinePhase = 'collecting' | 'baseline-ending' | 'anomaly-monitoring'

export interface FaceTestStatusState {
  phase: FaceBaselinePhase
}

export function createFaceTestStatusState(): FaceTestStatusState {
  return {
    phase: 'collecting',
  }
}

export function requestBaselineEnd(state: FaceTestStatusState): FaceTestStatusState {
  if (state.phase !== 'collecting') {
    return state
  }

  return {
    phase: 'baseline-ending',
  }
}

export function consumeFaceTestStatus(state: FaceTestStatusState): {
  state: FaceTestStatusState
  testStatus: FaceTestStatus
} {
  if (state.phase === 'baseline-ending') {
    return {
      state: {
        phase: 'anomaly-monitoring',
      },
      testStatus: 1,
    }
  }

  if (state.phase === 'anomaly-monitoring') {
    return {
      state,
      testStatus: 1,
    }
  }

  return {
    state,
    testStatus: 0,
  }
}

export function resetFaceTestStatusState(_state?: FaceTestStatusState): FaceTestStatusState {
  return createFaceTestStatusState()
}
