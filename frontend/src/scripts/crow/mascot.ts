import { ANIMATIONS, sayAnimation, WALK_ACROSS_END, type Animation, type AnimationName } from "./animations";
import { askAlreadyShown, rememberAskShown } from "./ask-memory";
import { clamp, ease } from "./motion";
import { blendPoses, restPose, type Pose } from "./pose";
import { register, restore, suppressOthers, unregister, type Suppressible } from "./registry";
import { renderBubble, renderPose, offsetPx, RIG_ASPECT } from "./render";
import { buildRig, type Parts } from "./rig";

export interface CrowOptions {
  assetPath?: string;
  anchor?: HTMLElement | "bottom-right" | "bottom-left";
  align?: "center" | "right";
  width?: number;
  speed?: number;
  followCursor?: boolean;
  idleSeconds?: number;
  idleAnim?: AnimationName;
  onClick?: (crow: CrowMascot) => void;
  zIndex?: number;
  solo?: boolean;
}

const DEFAULT_ASSET_PATH = "/images/crow/";
const DEFAULT_WIDTH = 260;
const DEFAULT_IDLE_SECONDS = 14;
const DEFAULT_Z_INDEX = 40;
const SCALE_BASE = 200;
const BLEND_SECONDS = 0.28;
const RECT_REFRESH_SECONDS = 0.4;
const HIDE_DELAY_MS = 240;
const VISIBILITY_MARGIN = "120px";
const SAY_NAME = "_say";

const reducedMotion = (): boolean => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const seconds = (): number => performance.now() / 1000;

export class CrowMascot implements Suppressible {
  hidden = false;
  private readonly host = document.createElement("div");
  private readonly stage: HTMLElement;
  private readonly parts: Parts;
  private readonly reduced = reducedMotion();
  private readonly width: number;
  private readonly speed: number;
  private readonly followCursor: boolean;
  private readonly idleSeconds: number;
  private readonly idleAnim: AnimationName;
  private readonly onClick: ((crow: CrowMascot) => void) | undefined;
  private animationName: string;
  private animation: Animation;
  private t0: number | null = null;
  private mouse: { x: number; y: number } | null = null;
  private lastActive = seconds();
  private visible = true;
  private holdRx = 0;
  private previous: string | null = null;
  private blendFrom: Pose | null = null;
  private blendT = 0;
  private lastPose: Pose | null = null;
  private rect: DOMRect | null = null;
  private rectT = 0;
  private raf = 0;
  private hideTimer = 0;
  private walkInTimer = 0;
  private readonly observer: IntersectionObserver;
  private suppressed: Suppressible[];

  constructor(options: CrowOptions = {}) {
    this.width = options.width ?? DEFAULT_WIDTH;
    this.speed = options.speed ?? 1;
    this.followCursor = options.followCursor !== false;
    this.idleSeconds = options.idleSeconds ?? DEFAULT_IDLE_SECONDS;
    this.idleAnim = options.idleAnim ?? "askQ";
    this.onClick = options.onClick;
    this.animationName = this.reduced ? "idle" : "runIn";
    this.animation = ANIMATIONS[this.reduced ? "idle" : "runIn"];
    const rig = buildRig(options.assetPath ?? DEFAULT_ASSET_PATH);
    this.stage = rig.stage;
    this.parts = rig.parts;
    this.mount(options);
    this.observer = this.watchVisibility();
    this.bindActivity();
    register(this);
    this.suppressed = options.solo === false ? [] : suppressOthers(this);
    this.start();
  }

  play(name: AnimationName): void {
    this.switchTo(name, ANIMATIONS[name]);
  }

  say(text: string): void {
    this.switchTo(SAY_NAME, sayAnimation(text));
  }

  walkIn(skipWalk: boolean): void {
    if (this.reduced) {
      this.parts.bubbleText.textContent = ANIMATIONS.invite.text;
      this.parts.bubble.style.opacity = "1";
      return;
    }
    if (skipWalk) {
      this.play("invite");
      return;
    }
    this.play("walkAcross");
    window.clearTimeout(this.walkInTimer);
    this.walkInTimer = window.setTimeout(() => {
      if (this.animationName !== "walkAcross") {
        return;
      }
      this.holdRx = WALK_ACROSS_END;
      this.play("invite");
    }, (ANIMATIONS.walkAcross.dur * 1000) / this.speed);
  }

  hide(): void {
    if (this.hidden) {
      return;
    }
    this.hidden = true;
    window.clearTimeout(this.hideTimer);
    if (this.reduced) {
      this.host.style.display = "none";
      return;
    }
    this.host.style.opacity = "0";
    this.host.style.transform = "translateY(10px) scale(.94)";
    this.hideTimer = window.setTimeout(() => {
      if (this.hidden) {
        this.host.style.display = "none";
      }
    }, HIDE_DELAY_MS);
  }

  show(): void {
    if (!this.hidden) {
      return;
    }
    this.hidden = false;
    window.clearTimeout(this.hideTimer);
    this.host.style.display = "";
    if (this.reduced) {
      return;
    }
    void this.host.offsetWidth;
    this.host.style.opacity = "1";
    this.host.style.transform = "";
  }

  destroy(): void {
    cancelAnimationFrame(this.raf);
    window.removeEventListener("pointermove", this.onMove);
    window.removeEventListener("scroll", this.onActivity);
    window.removeEventListener("keydown", this.onActivity);
    this.observer.disconnect();
    window.clearTimeout(this.hideTimer);
    window.clearTimeout(this.walkInTimer);
    this.host.remove();
    unregister(this);
    restore(this.suppressed);
    this.suppressed = [];
  }

  private mount(options: CrowOptions): void {
    const anchor = options.anchor ?? "bottom-right";
    this.host.className = "crow-mascot";
    this.host.style.width = `${String(this.width)}px`;
    this.host.style.height = `${String(Math.round(this.width * RIG_ASPECT))}px`;
    this.host.style.zIndex = String(options.zIndex ?? DEFAULT_Z_INDEX);
    this.host.style.setProperty("--crow-k", (this.width / SCALE_BASE).toFixed(4));
    this.host.append(this.stage);
    this.host.addEventListener("click", () => {
      this.handleClick();
    });
    if (anchor instanceof HTMLElement) {
      this.host.classList.add("is-anchored");
      this.host.classList.toggle("is-right", options.align === "right");
      anchor.append(this.host);
      return;
    }
    this.host.classList.add("is-fixed");
    this.host.classList.toggle("is-left", anchor === "bottom-left");
    document.body.append(this.host);
  }

  private handleClick(): void {
    if (this.onClick) {
      this.onClick(this);
      return;
    }
    this.play(Math.random() < 0.5 ? "nod" : "askQ");
  }

  private readonly onMove = (event: PointerEvent): void => {
    this.mouse = { x: event.clientX, y: event.clientY };
    this.lastActive = seconds();
  };

  private readonly onActivity = (): void => {
    this.lastActive = seconds();
  };

  private bindActivity(): void {
    window.addEventListener("pointermove", this.onMove, { passive: true });
    window.addEventListener("scroll", this.onActivity, { passive: true });
    window.addEventListener("keydown", this.onActivity, { passive: true });
  }

  private watchVisibility(): IntersectionObserver {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          this.visible = entry.isIntersecting;
        });
      },
      { rootMargin: VISIBILITY_MARGIN },
    );
    observer.observe(this.stage);
    return observer;
  }

  private start(): void {
    if (this.reduced) {
      const pose = restPose();
      ANIMATIONS.idle.fn(0, pose);
      renderPose(this.parts, pose);
      return;
    }
    this.raf = requestAnimationFrame(this.frame);
  }

  private readonly frame = (now: number): void => {
    this.tick(now / 1000);
    this.raf = requestAnimationFrame(this.frame);
  };

  private switchTo(name: string, animation: Animation): void {
    this.animationName = name;
    this.animation = animation;
    this.t0 = null;
  }

  private maybeAsk(now: number): void {
    if (this.animationName !== "idle" || this.idleSeconds <= 0 || now - this.lastActive <= this.idleSeconds) {
      return;
    }
    this.lastActive = now;
    if (!askAlreadyShown()) {
      rememberAskShown();
      this.play(this.idleAnim);
    }
  }

  private localTime(now: number): number {
    this.t0 ??= now;
    let t = (now - this.t0) * this.speed;
    if (!this.animation.loop && t > this.animation.dur) {
      this.switchTo("idle", ANIMATIONS.idle);
      this.t0 = now;
      t = 0;
    } else if (this.animation.loop && t > this.animation.dur) {
      t = t % this.animation.dur;
      this.t0 = now - t / this.speed;
    }
    return t;
  }

  private trackCursor(now: number, p: Pose): void {
    if (!this.followCursor || this.animation.track === false || !this.mouse) {
      return;
    }
    if (!this.rect || now - this.rectT > RECT_REFRESH_SECONDS) {
      this.rect = this.stage.getBoundingClientRect();
      this.rectT = now;
    }
    const cx = this.rect.left + this.rect.width * 0.52;
    const cy = this.rect.top + this.rect.height * 0.33;
    const dx = clamp((this.mouse.x - cx) / 320, -1, 1);
    const dy = clamp((this.mouse.y - cy) / 280, -1, 1);
    p.ex += dx * 7;
    p.ey += dy * 6;
    p.hrot += dx * 4.2;
    p.hx += dx * 15;
    p.hy += dy * 9;
  }

  private blend(now: number, p: Pose): Pose {
    if (this.previous !== this.animationName) {
      this.blendFrom = this.lastPose ? { ...this.lastPose } : null;
      this.blendT = now;
      this.previous = this.animationName;
    }
    if (!this.blendFrom) {
      return p;
    }
    const k = ease((now - this.blendT) / BLEND_SECONDS);
    if (k >= 1) {
      this.blendFrom = null;
      return p;
    }
    return blendPoses(this.blendFrom, p, k);
  }

  private tick(now: number): void {
    if (!this.visible) {
      return;
    }
    this.maybeAsk(now);
    const t = this.localTime(now);
    const p = restPose();
    this.animation.fn(t, p);
    if (this.holdRx && this.animationName !== "walkAcross") {
      p.rx += this.holdRx;
    }
    this.trackCursor(now, p);
    const pose = this.blend(now, p);
    this.lastPose = pose;
    renderPose(this.parts, pose);
    renderBubble(this.parts, this.animation, t, offsetPx(pose, this.width));
  }
}
