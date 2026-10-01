export const PARTS = ["bubble", "bubbleText", "root", "shadow", "char", "head", "eyeL", "eyeR", "arm", "legR", "legL", "jaw", "beak"] as const;

export type PartName = (typeof PARTS)[number];
export type Parts = Record<PartName, HTMLElement>;

const DEFAULT_BUBBLE_TEXT = "Чем помочь?";

function box(className: string, ...children: HTMLElement[]): HTMLElement {
  const node = document.createElement("div");
  node.className = className;
  node.append(...children);
  return node;
}

function picture(assetPath: string, file: string, className: string): HTMLImageElement {
  const image = document.createElement("img");
  image.src = `${assetPath}${file}.webp`;
  image.alt = "";
  image.className = className;
  image.draggable = false;
  return image;
}

function bubble(): { node: HTMLElement; text: HTMLElement } {
  const text = document.createElement("span");
  text.textContent = DEFAULT_BUBBLE_TEXT;
  const tail = box("crow-bubble-tail", box("crow-bubble-tail-edge"), box("crow-bubble-tail-fill"));
  return { node: box("crow-bubble", box("crow-bubble-box", text, tail)), text };
}

export function buildRig(assetPath: string): { stage: HTMLElement; parts: Parts } {
  const img = (file: string, className: string): HTMLImageElement => picture(assetPath, file, className);
  const speech = bubble();
  const eyeL = img("eyeL", "crow-eye-l");
  const eyeR = img("eyeR", "crow-eye-r");
  const head = box("crow-head", img("head", "crow-head-img"), eyeL, eyeR);
  const arm = box("crow-arm", img("arm", "crow-arm-img"));
  const legR = img("legR", "crow-leg-r");
  const legL = img("legL", "crow-leg-l");
  const beak = img("beak", "crow-beak");
  const jaw = box("crow-jaw", img("mouth", "crow-mouth"), beak);
  const char = box("crow-char", img("torso", "crow-full"), img("neck", "crow-full"), head, arm, legR, legL, img("body", "crow-body"), jaw);
  const shadow = box("crow-shadow");
  const root = box("crow-root", shadow, char);
  const stage = box("crow-stage", speech.node, root);
  stage.dataset.rig = "crow";
  return {
    stage,
    parts: { bubble: speech.node, bubbleText: speech.text, root, shadow, char, head, eyeL, eyeR, arm, legR, legL, jaw, beak },
  };
}
