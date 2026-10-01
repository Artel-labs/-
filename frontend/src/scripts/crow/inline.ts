import type { AnimationName } from "./animations";
import { CrowMascot } from "./mascot";

const DONE_WIDTH = 140;
const EMPTY_WIDTH = 160;
const VISIBLE_CLASS = "visible";

interface InlineCrow {
  width: number;
  solo: boolean;
  animation: AnimationName;
}

function mountInlineCrow(anchor: HTMLElement, { width, solo, animation }: InlineCrow): CrowMascot {
  const crow = new CrowMascot({ anchor, width, followCursor: false, idleSeconds: 0, solo, onClick: () => undefined });
  crow.play(animation);
  return crow;
}

export function mountDoneCrow(anchor: HTMLElement): CrowMascot {
  return mountInlineCrow(anchor, { width: DONE_WIDTH, solo: true, animation: "jump" });
}

export function emptyCrowToggle(empty: HTMLElement): (isEmpty: boolean) => void {
  let crow: CrowMascot | null = null;
  return (isEmpty) => {
    const slot = empty.querySelector<HTMLElement>("[data-crow-slot]");
    if (isEmpty && slot && !crow && empty.classList.contains(VISIBLE_CLASS)) {
      crow = mountInlineCrow(slot, { width: EMPTY_WIDTH, solo: false, animation: "inspect" });
    } else if (!isEmpty && crow) {
      crow.destroy();
      crow = null;
    }
  };
}
