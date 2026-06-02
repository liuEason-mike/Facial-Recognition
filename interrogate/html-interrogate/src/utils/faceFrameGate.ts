export interface FaceFrameGateInput {
  force?: boolean
  inFlight: boolean
}

export function shouldSendFaceFrame(input: FaceFrameGateInput) {
  return Boolean(input.force) || !input.inFlight
}
