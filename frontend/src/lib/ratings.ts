import data from "../data/ratings.json";

export interface RatingRow {
  year: string;
  field: string;
  place: string | null;
  url: string | null;
}

export interface Rating {
  title: string;
  rows: RatingRow[];
}

export const ratings: Rating[] = data;
