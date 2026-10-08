export interface FilterTag {
  group: string;
  value: string;
  name: string;
}

export interface TagHandlers {
  remove: (tag: FilterTag) => void;
  reset: () => void;
}

function tagButton(tag: FilterTag, handlers: TagHandlers): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "filter-tag";
  button.setAttribute("aria-label", `Убрать фильтр: ${tag.name}`);
  const name = document.createElement("span");
  name.textContent = tag.name;
  const cross = document.createElement("span");
  cross.className = "filter-tag-cross";
  cross.setAttribute("aria-hidden", "true");
  cross.textContent = "✕";
  button.append(name, cross);
  button.addEventListener("click", () => {
    handlers.remove(tag);
  });
  return button;
}

function resetButton(handlers: TagHandlers): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "filter-tags-reset";
  button.textContent = "Сбросить всё";
  button.addEventListener("click", handlers.reset);
  return button;
}

export function renderTags(container: HTMLElement, tags: FilterTag[], handlers: TagHandlers): void {
  container.replaceChildren(...tags.map((tag) => tagButton(tag, handlers)));
  if (tags.length > 0) {
    container.append(resetButton(handlers));
  }
  container.hidden = tags.length === 0;
}
