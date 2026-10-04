export const ICON_PATHS = {
  "arrow-right": "M3 8h10M9 4l4 4-4 4",
  "arrow-left": "M13 8H3M7 4L3 8l4 4",
  "arrow-up-right": "M5 11l6-6M6 5h5v5",
  check: "M3 8.5l3 3 7-7",
  search: "M7 12A5 5 0 1 0 7 2a5 5 0 0 0 0 10ZM10.7 10.7 14 14",
} as const;

export type IconName = keyof typeof ICON_PATHS;

export const ICON_VIEWBOX = "0 0 16 16";
export const ICON_STROKE = "1.6";
