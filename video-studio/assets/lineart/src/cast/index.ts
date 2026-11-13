// Public API of the line-art cast bundle (lineart.js).
export { createLineStage, windAt, type LineStage, type StageOptions, type AddOptions } from './stage.ts';
export { createCharacter, type Character, type Spec, type Gesture } from './rig.ts';
export { ROSTER, byId } from './roster.ts';
export { SKINS, skinById, withSkin, type Skin } from './skins.ts';
export { el, pen, shape, blot, paint, limb, solid, inkDefs, f, pt, PEN, PAPER } from '../lib/ink.ts';
export { spring, pendulum, ease, clamp, lerp, smooth, wobble } from '../lib/motion.ts';
