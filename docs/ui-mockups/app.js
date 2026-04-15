const screens = [...document.querySelectorAll("[data-screen]")];
const navButtons = [...document.querySelectorAll("[data-screen-target]")];

const metaApp = document.getElementById("meta-app");
const metaTitle = document.getElementById("meta-title");
const metaRoute = document.getElementById("meta-route");
const metaNote = document.getElementById("meta-note");

function activateScreen(screenId, updateHash = true) {
  const screen = screens.find((item) => item.dataset.screen === screenId);
  if (!screen) return;

  screens.forEach((item) => {
    item.classList.toggle("active", item.dataset.screen === screenId);
  });

  navButtons.forEach((button) => {
    button.classList.toggle(
      "active",
      button.dataset.screenTarget === screenId,
    );
  });

  metaApp.textContent = screen.dataset.app;
  metaTitle.textContent = screen.dataset.title;
  metaRoute.textContent = screen.dataset.route;
  metaNote.textContent = screen.dataset.note;

  if (updateHash) {
    window.location.hash = screenId;
  }
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activateScreen(button.dataset.screenTarget);
  });
});

document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-jump]");
  if (!target) return;

  activateScreen(target.dataset.jump);
});

window.addEventListener("hashchange", () => {
  const nextId = window.location.hash.replace("#", "");
  if (nextId) {
    activateScreen(nextId, false);
  }
});

activateScreen(window.location.hash.replace("#", "") || "tester-login", false);
