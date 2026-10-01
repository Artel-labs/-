import type { TgCatalog, TgProgram } from "../../lib/tg";
import type { Bridge } from "./bridge";
import type { ApplicationDraft, Values } from "./core.ts";

export type ScreenName = "list" | "program" | "form" | "demo";
export type Direction = "forward" | "back";

export interface State {
  stack: ScreenName[];
  sphere: string;
  query: string;
  listScroll: number;
  programId: string | null;
  campaign: string | null;
  submitted: Values | null;
  nameFromTelegram: boolean;
  form: ApplicationDraft;
}

export interface Context {
  data: TgCatalog;
  state: State;
  bridge: Bridge;
  program(): TgProgram;
  go(name: ScreenName): void;
  reset(name: ScreenName): void;
}
