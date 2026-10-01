export interface BotProgram {
  id: string;
  title: string;
  url: string;
  sphere: string;
  type: string;
  format: string;
  format_label: string;
  price: number | null;
  price_label: string;
  duration: string | null;
  hours: string | null;
  schedule: string | null;
  start: string | null;
  start_iso: string | null;
  keywords: string[];
}

export interface FaqEntry {
  id: string;
  triggers: string[];
  text: string;
  anchor: string;
  note?: string;
}

export interface FaqGap {
  id: string;
  triggers: string[];
}

export interface FaqDuration {
  id: string;
  triggers: string[];
  anchor: string;
}

export interface Faq {
  answers: FaqEntry[];
  gaps: FaqGap[];
  duration: FaqDuration;
}

export interface BotData extends Faq {
  programs: BotProgram[];
}
