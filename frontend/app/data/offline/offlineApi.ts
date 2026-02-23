// Redirect consolidated offline API to the central studyMock to reduce duplicate files
export type {
  OfflinePillarsPayload,
  OfflineSentimentsPayload,
  OfflinePlayerExpectationsPayload,
} from '~/studyMock'
export { getOfflinePillars, getOfflineSentiments, getOfflinePlayerExpectations } from '~/studyMock'
