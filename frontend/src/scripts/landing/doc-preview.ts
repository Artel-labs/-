import { closeButton, element, openDialog } from "../dialog";

const DEFAULT_EXTENSION = "png";
const DEFAULT_HEIGHT = "848";
const DEFAULT_LABEL = "Образец документа";
const IMAGE_WIDTH = "1200";

function figure(base: string, extension: string, height: string, label: string): HTMLElement {
  const wrapper = element("figure", "doc-figure");
  const picture = element("picture");
  const source = element("source");
  source.srcset = `${base}.webp`;
  source.type = "image/webp";
  const image = element("img");
  image.width = Number(IMAGE_WIDTH);
  image.height = Number(height);
  image.decoding = "async";
  image.alt = `Образец бланка: ${label}`;
  image.src = `${base}.${extension}`;
  picture.append(source, image);
  wrapper.appendChild(picture);
  return wrapper;
}

function open(button: HTMLElement): void {
  const base = button.dataset.docPreview ?? "";
  const label = button.dataset.docLabel ?? DEFAULT_LABEL;
  const windowNode = element("div", "doc-window");
  windowNode.setAttribute("role", "dialog");
  windowNode.setAttribute("aria-modal", "true");
  windowNode.setAttribute("aria-labelledby", "doc-title");
  const title = element("h2", "", `Образец: ${label}`);
  title.id = "doc-title";
  title.tabIndex = -1;
  const close = closeButton("doc-close", "Закрыть образец");
  windowNode.append(
    close,
    title,
    figure(base, button.dataset.docExt ?? DEFAULT_EXTENSION, button.dataset.docHeight ?? DEFAULT_HEIGHT, label),
    element("p", "doc-note", "Незаполненный образец бланка НИУ ВШЭ."),
  );
  const backdrop = element("div", "doc-backdrop");
  backdrop.appendChild(windowNode);
  const dialog = openDialog({ backdrop, initialFocus: title });
  close.addEventListener("click", () => {
    dialog.close();
  });
}

export function setupDocPreview(): void {
  document.addEventListener("click", (event) => {
    const button = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-doc-preview]") : null;
    if (button) {
      event.preventDefault();
      open(button);
    }
  });
}
