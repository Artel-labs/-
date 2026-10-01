const EMAIL_PART = '[^\\s@,;?#%/\\\\<>"&=:]';
const EMAIL_SHAPE = new RegExp(`^${EMAIL_PART}+@${EMAIL_PART}+\\.${EMAIL_PART}{2,}$`);
const PHONE_ALLOWED = /^[0-9+()\-\s.]+$/;
const PHONE_MIN_DIGITS = 10;
const PHONE_MAX_DIGITS = 15;

export const EMAIL_TYPO = "Проверьте адрес почты: похоже, в нём опечатка.";
export const PHONE_BAD_CHARS = "В телефоне допустимы только цифры, пробелы и знаки + ( ) -";
export const PHONE_BAD_LENGTH = "Проверьте телефон: нужен номер с кодом страны или города.";

export function emailLooksValid(value: string): boolean {
  return EMAIL_SHAPE.test(value);
}

export function phoneProblem(value: string): string {
  if (!PHONE_ALLOWED.test(value)) {
    return PHONE_BAD_CHARS;
  }
  const digits = value.replace(/\D/g, "").length;
  return digits < PHONE_MIN_DIGITS || digits > PHONE_MAX_DIGITS ? PHONE_BAD_LENGTH : "";
}
