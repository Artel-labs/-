import type { TgCatalog, TgProgram } from "../../lib/tg";
import { Bridge } from "./bridge";
import type { Context, Direction, ScreenName, State } from "./context";
import { parseStartParam } from "./core.ts";
import { demoScreen } from "./demo-screen";
import { formScreen } from "./form-screen";
import { listScreen } from "./list-screen";
import { programScreen } from "./program-screen";

const SCREENS: Record<ScreenName, (context: Context, direction: Direction) => HTMLElement> = {
  list: listScreen,
  program: programScreen,
  form: formScreen,
  demo: demoScreen,
};

function readCatalog(): TgCatalog {
  return JSON.parse(document.getElementById("tg-data")?.textContent ?? "{}") as TgCatalog;
}

function initialState(bridge: Bridge, campaign: string | null): State {
  const user = bridge.user();
  return {
    stack: [],
    sphere: "all",
    query: "",
    listScroll: 0,
    programId: null,
    campaign,
    submitted: null,
    nameFromTelegram: Boolean(user?.first_name),
    form: { firstName: user?.first_name ?? "", lastName: user?.last_name ?? "", phone: "", email: "", position: "", company: "", consent: false },
  };
}

class TgApp implements Context {
  readonly data = readCatalog();
  readonly bridge = new Bridge();
  readonly state: State;
  private readonly byId = new Map<string, TgProgram>(this.data.programs.map((program) => [program.id, program]));
  private readonly root = document.getElementById("app");
  private firstShow = true;

  constructor() {
    const start = parseStartParam(this.bridge.startParam(), [...this.byId.keys()]);
    this.state = initialState(this.bridge, start.campaign);
    this.bridge.connect(() => {
      this.back();
    });
    if (start.programId) {
      this.state.programId = start.programId;
      this.state.stack = ["list"];
      this.go("program");
    } else {
      this.reset("list");
    }
  }

  program(): TgProgram {
    const found = this.byId.get(this.state.programId ?? "");
    if (!found) {
      throw new Error("Программа не выбрана");
    }
    return found;
  }

  go(name: ScreenName): void {
    if (this.current() === "list") {
      this.state.listScroll = window.scrollY;
    }
    this.state.stack.push(name);
    this.show(name, "forward");
  }

  reset(name: ScreenName): void {
    this.state.stack = [name];
    this.show(name, "forward");
  }

  private back(): void {
    if (this.state.stack.length < 2) {
      return;
    }
    this.state.stack.pop();
    this.show(this.current() ?? "list", "back");
  }

  private current(): ScreenName | undefined {
    return this.state.stack.at(-1);
  }

  private show(requested: ScreenName, direction: Direction): void {
    let name = requested;
    if (name !== "list" && !this.byId.has(this.state.programId ?? "")) {
      this.state.stack = ["list"];
      name = "list";
    }
    const screen = SCREENS[name](this, direction);
    screen.classList.add("screen", "in");
    if (direction === "back") {
      screen.classList.add("back");
    }
    this.root?.replaceChildren(screen);
    window.scrollTo(0, name === "list" && direction === "back" ? this.state.listScroll : 0);
    this.bridge.setBack(this.state.stack.length > 1);
    this.focusHeading(screen);
  }

  private focusHeading(screen: HTMLElement): void {
    if (this.firstShow) {
      this.firstShow = false;
      return;
    }
    const heading = screen.querySelector("h1");
    heading?.setAttribute("tabindex", "-1");
    heading?.focus({ preventScroll: true });
  }
}

export function startTgApp(): void {
  new TgApp();
}
