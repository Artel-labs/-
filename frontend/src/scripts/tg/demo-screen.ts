import type { Context } from "./context";
import { h } from "./dom";

function summaryRows(context: Context): [string, string][] {
  const { state, bridge } = context;
  const values = state.submitted;
  if (!values) {
    return [];
  }
  return [
    ["Программа", context.program().title],
    ["Имя", `${values.firstName} ${values.lastName}`],
    ["Телефон", values.phone],
    ["E-mail", values.email],
    ...(values.position ? [["Должность", values.position] as [string, string]] : []),
    ...(values.company ? [["Место работы", values.company] as [string, string]] : []),
    ...(state.campaign ? [["Метка", state.campaign] as [string, string]] : []),
    ["Откуда", bridge.inTelegram ? "Telegram, мини-приложение" : "Мини-приложение в браузере"],
  ];
}

export function demoScreen(context: Context): HTMLElement {
  const program = context.program();
  context.bridge.setMain(program.pay ? "Перейти к оплате на hse.ru" : null, () => {
    context.bridge.open(program.pay);
  });
  const again = h("button", { class: "ghost", type: "button", text: "Вернуться к программам" });
  again.addEventListener("click", () => {
    context.state.listScroll = 0;
    context.state.form.consent = false;
    context.state.submitted = null;
    context.reset("list");
  });
  return h("section", { "aria-label": "Заявка готова" }, [
    h("h1", { class: "h1 h1--sm", text: "Заявка готова" }),
    h("div", { class: "plaque", role: "status" }, [
      h("b", { text: "Демо: заявка не отправлена" }),
      h("p", { text: "В рабочей версии эти данные уйдут в учебный офис Центра ДПО факультета права, и менеджер свяжется с вами. Сейчас они не покидают телефон." }),
    ]),
    h("dl", { class: "summary" }, summaryRows(context).map(([label, value]) => h("div", null, [h("dt", { text: label }), h("dd", { text: value })]))),
    again,
  ]);
}
