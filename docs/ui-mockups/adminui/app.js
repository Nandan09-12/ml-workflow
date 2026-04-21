const pageTitles = {
  dashboard: "Dashboard",
  "daily-submissions": "Daily Submissions",
  "submission-detail": "Daily Submission Detail",
  workorders: "Workorders",
  "workorder-detail": "Workorder Detail",
  users: "Users",
  "pending-users": "Pending Users",
  "no-submission-yet": "No Submission Yet",
  reports: "Reports",
};

const workorders = [
  {
    code: "WO-NE-401",
    region: "NE-UP",
    total: 145,
    completed: 91,
    skipped: 8,
    remaining: 46,
    progress: 68,
    status: "ACTIVE",
  },
  {
    code: "WO-SF-118",
    region: "South/Florida",
    total: 92,
    completed: 72,
    skipped: 2,
    remaining: 18,
    progress: 80,
    status: "ACTIVE",
  },
  {
    code: "WO-CT-072",
    region: "Central",
    total: 58,
    completed: 51,
    skipped: 7,
    remaining: 0,
    progress: 100,
    status: "COMPLETED",
  },
  {
    code: "WO-NE-389",
    region: "NE-UP",
    total: 110,
    completed: 60,
    skipped: 11,
    remaining: 39,
    progress: 65,
    status: "ACTIVE",
  },
];

const submissions = [
  {
    date: "Apr 20",
    time: "05:41 PM",
    tester: "Priya Shah",
    email: "priya@mltech.com",
    workorder: "WO-SF-118",
    region: "South/Florida",
    shift: "PM",
    ticket: "TKT-9031",
    completed: 27,
    skipped: 2,
    force: 4,
    status: "CHECKED_OUT",
    file: "File Pending",
  },
  {
    date: "Apr 20",
    time: "04:55 PM",
    tester: "Jane Doe",
    email: "jane@mltech.com",
    workorder: "WO-NE-401",
    region: "NE-UP",
    shift: "AM",
    ticket: "TKT-8712",
    completed: 38,
    skipped: 1,
    force: 3,
    status: "COMPLETED",
    file: "Attached",
  },
  {
    date: "Apr 20",
    time: "03:20 PM",
    tester: "Nina Patel",
    email: "nina@mltech.com",
    workorder: "WO-NE-401",
    region: "NE-UP",
    shift: "AM",
    ticket: "TKT-8815",
    completed: 23,
    skipped: 3,
    force: 1,
    status: "IN_PROGRESS",
    file: "Not Required",
  },
  {
    date: "Apr 20",
    time: "02:52 PM",
    tester: "Arun Mehta",
    email: "arun@mltech.com",
    workorder: "WO-CT-072",
    region: "Central",
    shift: "PM",
    ticket: "TKT-8640",
    completed: 51,
    skipped: 7,
    force: 6,
    status: "COMPLETED",
    file: "Attached",
  },
  {
    date: "Apr 20",
    time: "01:18 PM",
    tester: "Maria Lee",
    email: "maria@mltech.com",
    workorder: "WO-NE-389",
    region: "NE-UP",
    shift: "AM",
    ticket: "TKT-8938",
    completed: 18,
    skipped: 0,
    force: 2,
    status: "CHECKED_OUT",
    file: "File Pending",
  },
];

const users = [
  {
    name: "Asha Kumar",
    email: "asha@mltech.com",
    requested: "ADMIN",
    approved: "ADMIN",
    status: "APPROVED",
    login: "Today, 08:02 AM",
  },
  {
    name: "Jane Doe",
    email: "jane@mltech.com",
    requested: "DRIVE_TESTER",
    approved: "DRIVE_TESTER",
    status: "APPROVED",
    login: "Today, 05:02 PM",
  },
  {
    name: "Priya Shah",
    email: "priya@mltech.com",
    requested: "DRIVE_TESTER",
    approved: "DRIVE_TESTER",
    status: "APPROVED",
    login: "Today, 05:46 PM",
  },
  {
    name: "Chris Hall",
    email: "chris@mltech.com",
    requested: "DRIVE_TESTER",
    approved: "DRIVE_TESTER",
    status: "APPROVED",
    login: "Yesterday, 06:12 PM",
  },
  {
    name: "Leah Ford",
    email: "leah@mltech.com",
    requested: "DRIVE_TESTER",
    approved: "-",
    status: "PENDING_APPROVAL",
    login: "-",
  },
];

const pendingUsers = [
  {
    name: "Leah Ford",
    email: "leah@mltech.com",
    role: "DRIVE_TESTER",
    requested: "Apr 20, 2026, 09:14 AM",
    note: "New drive tester account awaiting approval.",
  },
  {
    name: "Mohammed Khan",
    email: "mohammed@mltech.com",
    role: "DRIVE_TESTER",
    requested: "Apr 20, 2026, 10:02 AM",
    note: "Pending access for the DT Check-in tester app.",
  },
  {
    name: "Iris Chen",
    email: "iris@mltech.com",
    role: "ADMIN",
    requested: "Apr 19, 2026, 04:44 PM",
    note: "Admin request should be reviewed carefully.",
  },
  {
    name: "Victor Neal",
    email: "victor@mltech.com",
    role: "DRIVE_TESTER",
    requested: "Apr 19, 2026, 03:31 PM",
    note: "Pending approval since yesterday.",
  },
];

const noSubmissionYet = [
  {
    name: "Chris Hall",
    email: "chris@mltech.com",
    role: "DRIVE_TESTER",
    lastDate: "Apr 19, 2026",
    workorder: "WO-NE-362",
  },
  {
    name: "Sofia Romero",
    email: "sofia@mltech.com",
    role: "DRIVE_TESTER",
    lastDate: "Apr 18, 2026",
    workorder: "WO-SF-102",
  },
  {
    name: "Dev Patel",
    email: "dev@mltech.com",
    role: "DRIVE_TESTER",
    lastDate: "Apr 18, 2026",
    workorder: "WO-CT-055",
  },
  {
    name: "Ken Brooks",
    email: "ken@mltech.com",
    role: "DRIVE_TESTER",
    lastDate: "Apr 17, 2026",
    workorder: "WO-NE-344",
  },
];

function badgeClass(value) {
  if (["COMPLETED", "APPROVED", "Attached"].includes(value)) return "success";
  if (["CHECKED_OUT", "File Pending", "PENDING_APPROVAL"].includes(value)) return "warning";
  if (["SUSPENDED", "REJECTED"].includes(value)) return "danger";
  if (["ACTIVE", "IN_PROGRESS", "ADMIN", "DRIVE_TESTER"].includes(value)) return "neutral";
  return "muted";
}

function badge(value) {
  return `<span class="badge ${badgeClass(value)}">${value}</span>`;
}

function goToPage(pageId, updateHash = true) {
  const page = document.querySelector(`[data-page="${pageId}"]`);
  if (!page) return;

  document.querySelectorAll("[data-page]").forEach((item) => {
    item.classList.toggle("active", item.dataset.page === pageId);
  });

  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.nav === pageId);
  });

  document.getElementById("page-title").textContent = pageTitles[pageId] || "Dashboard";

  if (updateHash) {
    window.location.hash = pageId;
  }
}

function renderDashboardWorkorders() {
  const container = document.getElementById("dashboard-workorders");
  container.innerHTML = workorders
    .slice(0, 4)
    .map(
      (item) => `
        <article class="progress-card">
          <div class="progress-card-head">
            <strong>${item.code}</strong>
            ${badge(item.status)}
          </div>
          <div class="progress-bar"><span style="width: ${item.progress}%"></span></div>
          <div class="progress-card-foot">
            <span>${item.region}</span>
            <span>${item.remaining} remaining</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderRecentSubmissions() {
  const tbody = document.getElementById("recent-submissions");
  tbody.innerHTML = submissions
    .slice(0, 5)
    .map(
      (item) => `
        <tr>
          <td>${item.time}</td>
          <td>${item.tester}</td>
          <td>${item.workorder}</td>
          <td>${item.shift}</td>
          <td>${badge(item.status)}</td>
          <td>${badge(item.file)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderDailySubmissions() {
  const tbody = document.getElementById("daily-submissions-table");
  tbody.innerHTML = submissions
    .map(
      (item) => `
        <tr>
          <td>${item.date}</td>
          <td>
            <strong>${item.tester}</strong><br />
            <span class="muted">${item.email}</span>
          </td>
          <td>${item.workorder}</td>
          <td>${item.region}</td>
          <td>${item.shift}</td>
          <td>${item.completed}</td>
          <td>${item.skipped}</td>
          <td>${badge(item.status)}</td>
          <td>${badge(item.file)}</td>
          <td><button class="row-action" type="button" data-jump="submission-detail">View</button></td>
        </tr>
      `,
    )
    .join("");
}

function renderWorkorders() {
  const tbody = document.getElementById("workorders-table");
  tbody.innerHTML = workorders
    .map(
      (item) => `
        <tr>
          <td><strong>${item.code}</strong></td>
          <td>${item.region}</td>
          <td>${item.total}</td>
          <td>${item.completed}</td>
          <td>${item.skipped}</td>
          <td>${item.remaining}</td>
          <td>
            <div class="progress-bar"><span style="width: ${item.progress}%"></span></div>
            <span class="muted">${item.progress}%</span>
          </td>
          <td>${badge(item.status)}</td>
          <td><button class="row-action" type="button" data-jump="workorder-detail">View</button></td>
        </tr>
      `,
    )
    .join("");
}

function renderUsers() {
  const tbody = document.getElementById("users-table");
  tbody.innerHTML = users
    .map(
      (user) => `
        <tr>
          <td><strong>${user.name}</strong></td>
          <td>${user.email}</td>
          <td>${badge(user.requested)}</td>
          <td>${user.approved === "-" ? "-" : badge(user.approved)}</td>
          <td>${badge(user.status)}</td>
          <td>${user.login}</td>
          <td><button class="row-action" type="button">Details</button></td>
        </tr>
      `,
    )
    .join("");
}

function renderPendingUsers() {
  const container = document.getElementById("pending-users-list");
  container.innerHTML = pendingUsers
    .map(
      (user) => `
        <article class="approval-card">
          <div class="approval-card-head">
            <div>
              <h3>${user.name}</h3>
              <p>${user.email}</p>
            </div>
            ${badge(user.role)}
          </div>
          <p>${user.note}</p>
          <p>Requested ${user.requested}</p>
          <div class="button-row">
            <button class="primary-button" type="button">
              <svg viewBox="0 0 24 24"><path d="m9 16.2-3.5-3.5L4 14.2 9 19l11-11-1.5-1.5L9 16.2Z" /></svg>
              Approve
            </button>
            <button class="danger-button" type="button">
              <svg viewBox="0 0 24 24"><path d="m6.4 5 12.6 12.6-1.4 1.4L5 6.4 6.4 5Zm12.6 1.4L6.4 19 5 17.6 17.6 5 19 6.4Z" /></svg>
              Reject
            </button>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderNoSubmissionYet() {
  const tbody = document.getElementById("no-submission-table");
  tbody.innerHTML = noSubmissionYet
    .map(
      (user) => `
        <tr>
          <td><strong>${user.name}</strong></td>
          <td>${user.email}</td>
          <td>${badge(user.role)}</td>
          <td>${user.lastDate}</td>
          <td>${user.workorder}</td>
          <td><button class="row-action" type="button">Open User</button></td>
        </tr>
      `,
    )
    .join("");
}

function submissionEditForm() {
  return `
    <div class="impact-box">
      <strong>Admin edit</strong>
      <span>Changed daily counts can recompute the parent workorder progress and status.</span>
    </div>
    <div class="form-grid">
      <label>
        <span>Work date</span>
        <input type="date" value="2026-04-20" />
      </label>
      <label>
        <span>Shift</span>
        <select>
          <option selected>PM</option>
          <option>AM</option>
        </select>
      </label>
      <label class="full">
        <span>Ticket number</span>
        <input value="TKT-9031" />
      </label>
      <label>
        <span>Completed grids</span>
        <input type="number" value="27" />
      </label>
      <label>
        <span>Skipped grids</span>
        <input type="number" value="2" />
      </label>
      <label>
        <span>Force tested grids</span>
        <input type="number" value="4" />
      </label>
      <label>
        <span>Team number</span>
        <input value="" placeholder="Optional in admin UI" />
      </label>
      <label class="full">
        <span>Admin note</span>
        <input value="Corrected final EOD counts from closeout call." />
      </label>
    </div>
    <div class="button-row">
      <button class="primary-button" type="button">Save Changes</button>
      <button class="secondary-button" type="button" data-close-drawer>Cancel</button>
    </div>
  `;
}

function workorderEditForm() {
  return `
    <div class="impact-box">
      <strong>Workorder guardrails</strong>
      <span>Total grids cannot be reduced below aggregate completed plus skipped grids.</span>
    </div>
    <div class="form-grid">
      <label class="full">
        <span>Workorder code</span>
        <input value="WO-NE-401" />
      </label>
      <label>
        <span>Region</span>
        <select>
          <option selected>NE-UP</option>
          <option>Central</option>
          <option>South/Florida</option>
        </select>
      </label>
      <label>
        <span>Total grids</span>
        <input type="number" value="145" />
      </label>
      <label class="full">
        <span>Admin note</span>
        <input value="Adjusted grand total after admin verification." />
      </label>
    </div>
    <div class="button-row">
      <button class="primary-button" type="button">Save Workorder</button>
      <button class="secondary-button" type="button" data-close-drawer>Cancel</button>
    </div>
  `;
}

function openDrawer(kind) {
  const drawer = document.querySelector(".edit-drawer");
  const backdrop = document.querySelector(".drawer-backdrop");
  const title = document.getElementById("drawer-title");
  const kicker = document.getElementById("drawer-kicker");
  const body = document.getElementById("drawer-body");

  if (kind === "workorder") {
    kicker.textContent = "Workorder Edit";
    title.textContent = "Edit WO-NE-401";
    body.innerHTML = workorderEditForm();
  } else {
    kicker.textContent = "Submission Edit";
    title.textContent = "Edit Daily Submission";
    body.innerHTML = submissionEditForm();
  }

  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  backdrop.classList.add("open");
}

function closeDrawer() {
  const drawer = document.querySelector(".edit-drawer");
  const backdrop = document.querySelector(".drawer-backdrop");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
  backdrop.classList.remove("open");
}

function renderAll() {
  renderDashboardWorkorders();
  renderRecentSubmissions();
  renderDailySubmissions();
  renderWorkorders();
  renderUsers();
  renderPendingUsers();
  renderNoSubmissionYet();
}

document.addEventListener("click", (event) => {
  const jumpTarget = event.target.closest("[data-jump]");
  if (jumpTarget) {
    event.preventDefault();
    goToPage(jumpTarget.dataset.jump);
    return;
  }

  const navTarget = event.target.closest("[data-nav]");
  if (navTarget) {
    event.preventDefault();
    goToPage(navTarget.dataset.nav);
    return;
  }

  const drawerTarget = event.target.closest("[data-open-edit]");
  if (drawerTarget) {
    openDrawer(drawerTarget.dataset.openEdit);
    return;
  }

  if (event.target.closest("[data-close-drawer]")) {
    closeDrawer();
  }
});

window.addEventListener("hashchange", () => {
  const hashPage = window.location.hash.replace("#", "");
  if (hashPage) {
    goToPage(hashPage, false);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeDrawer();
  }
});

renderAll();
goToPage(window.location.hash.replace("#", "") || "dashboard", false);
