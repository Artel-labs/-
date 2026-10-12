import type { AnimationName } from "./animations";
import { CrowMascot } from "./mascot";

const EMPTY_WIDTH = 160;
const VISIBLE_CLASS = "visible";

interface InlineCrow {
  width: number;
  solo: boolean;
  animation: AnimationName;
}

function quietCrow(anchor: HTMLElement, width: number, solo: boolean): CrowMascot {
  return new CrowMascot({ anchor, width, followCursor: false, idleSeconds: 0, solo, onClick: () => undefined });
}

function mountInlineCrow(anchor: HTMLElement, { width, solo, animation }: InlineCrow): CrowMascot {
  const crow = quietCrow(anchor, width, solo);
  crow.play(animation);
  return crow;
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
