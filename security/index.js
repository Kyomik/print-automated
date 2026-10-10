import { env } from '../config/env.js';
import { createInspector } from './inspector.js';
import { detectType } from './checks/detect-type.check.js';
import { checkSize } from './checks/size.check.js';
import { checkMime } from './checks/mime.check.js';
import { checkTypeSpecific } from './checks/type-specific.check.js';
import { createClamavCheck } from './checks/clamav.check.js';

// Urutan: murah dulu, antivirus terakhir
export const inspectAttachment = createInspector([
  detectType,
  checkSize,
  checkMime,
  checkTypeSpecific,
  createClamavCheck(env.clamav),
]);