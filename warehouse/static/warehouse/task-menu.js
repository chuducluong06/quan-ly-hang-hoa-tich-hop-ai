(function () {
    const root = document.documentElement;
    const savedTheme = localStorage.getItem("warehouse-theme");
    if (savedTheme === "light" || savedTheme === "dark") {
        root.setAttribute("data-theme", savedTheme);
    }

    const menuTemplate = document.getElementById("taskMenuTemplate");
    const menuConfig = document.getElementById("taskMenuConfig");
    const existingSidebar = document.getElementById("sidebarNav");

    if (menuTemplate && menuConfig && !existingSidebar) {
        const legacyNavigation = Array.from(document.querySelectorAll(
            ".sidebar, body > aside, body > nav.navbar"
        ));
        const layoutRoots = new Set();

        legacyNavigation.forEach((navigation) => {
            navigation.classList.add("task-legacy-navigation");
            const parent = navigation.parentElement;
            if (parent && parent !== document.body) {
                layoutRoots.add(parent);
                const isNavCol = Array.from(navigation.classList).some((name) => /^col(?:-|$)/.test(name));
                const isParentCol = Array.from(parent.classList).some((name) => /^col(?:-|$)/.test(name));
                if (isNavCol || isParentCol) {
                    const colElement = isNavCol ? navigation : parent;
                    colElement.classList.add("task-legacy-column");
                    const container = colElement.parentElement;
                    if (container) {
                        layoutRoots.add(container);
                        Array.from(container.children).forEach((sibling) => {
                            if (sibling !== colElement) {
                                sibling.classList.add("task-main-area");
                                sibling.classList.remove("ms-sm-auto", "ms-auto");
                            }
                        });
                    }
                }
            }
        });

        const sidebar = menuTemplate.content.firstElementChild.cloneNode(true);
        document.body.prepend(sidebar);
        document.body.classList.add("has-task-sidebar");

        const bodyContent = Array.from(document.body.children).filter((element) =>
            element !== sidebar
            && element !== menuTemplate
            && element !== menuConfig
            && element.tagName !== "SCRIPT"
            && !element.classList.contains("task-legacy-navigation")
        );

        bodyContent.forEach((element) => element.classList.add("task-main-area"));
        layoutRoots.forEach((layout) => layout.classList.add("task-layout-root"));

        document.querySelectorAll("header.h-16, body > nav.navbar, .main-content > .d-flex.justify-content-between.align-items-center.bg-white")
            .forEach((header) => header.classList.add("task-legacy-header"));
        document.querySelectorAll("a[href]").forEach((link) => {
            if (!link.href.includes("/logout")) {
                return;
            }
            let parent = link.parentElement;
            for (let depth = 0; parent && parent !== document.body && depth < 6; depth += 1) {
                if (/justify-content-between|justify-between/.test(parent.className)) {
                    parent.classList.add("task-legacy-header");
                    break;
                }
                parent = parent.parentElement;
            }
        });

        const username = menuConfig.dataset.username || "Người dùng";
        const role = menuConfig.dataset.role || "";
        const globalSearchUrl = menuConfig.dataset.globalSearchUrl;
        sidebar.querySelector("[data-task-username]").textContent = username;
        sidebar.querySelector("[data-task-role]").textContent = role;
        sidebar.querySelector("[data-task-avatar]").textContent = username.slice(0, 1).toUpperCase();

        const toolbar = document.createElement("header");
        toolbar.className = "task-topbar";
        toolbar.innerHTML = `
            <form class="task-topbar-search" action="${globalSearchUrl}" method="get" role="search">
                <button type="submit" aria-label="Tìm kiếm">
                    <i class="bi bi-search" aria-hidden="true"></i>
                </button>
                <input type="search" name="q" aria-label="Tìm kiếm hàng hóa, phiếu nhập hoặc nhà cung cấp" placeholder="Tìm kiếm hàng hóa, phiếu nhập, nhà cung cấp..." required>
            </form>
            <div class="task-topbar-actions">
                <span class="task-topbar-date"></span>
                <span class="task-topbar-divider" aria-hidden="true"></span>
                <span class="task-user-avatar">${username.slice(0, 1).toUpperCase()}</span>
                <span class="task-topbar-user">
                    <strong></strong>
                    <small></small>
                </span>
                <a class="task-topbar-logout" href="${sidebar.querySelector(".task-sidebar-footer > a").href}" aria-label="Đăng xuất" title="Đăng xuất">
                    <i class="bi bi-box-arrow-right"></i>
                </a>
            </div>`;
        toolbar.querySelector(".task-topbar-date").textContent = new Intl.DateTimeFormat("vi-VN", {
            weekday: "short",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        }).format(new Date());
        toolbar.querySelector(".task-topbar-user strong").textContent = username;
        toolbar.querySelector(".task-topbar-user small").textContent = role;
        document.body.appendChild(toolbar);

        const toggle = document.createElement("button");
        toggle.className = "task-menu-toggle";
        toggle.type = "button";
        toggle.setAttribute("aria-label", "Mở menu");
        toggle.innerHTML = '<i class="bi bi-list"></i>';

        const overlay = document.createElement("button");
        overlay.className = "task-menu-overlay";
        overlay.type = "button";
        overlay.setAttribute("aria-label", "Đóng menu");
        document.body.append(toggle, overlay);

        const closeMenu = () => {
            sidebar.classList.remove("is-open");
            overlay.classList.remove("is-visible");
            toggle.setAttribute("aria-expanded", "false");
        };
        toggle.addEventListener("click", () => {
            const isOpen = sidebar.classList.toggle("is-open");
            overlay.classList.toggle("is-visible", isOpen);
            toggle.setAttribute("aria-expanded", String(isOpen));
        });
        overlay.addEventListener("click", closeMenu);

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeMenu();
            }
        });
        sidebar.querySelectorAll(".task-navigation a").forEach((link) => {
            link.addEventListener("click", closeMenu);
        });
    }

    const currentPath = window.location.pathname.replace(/\/+$/, "") || "/";
    const links = Array.from(document.querySelectorAll(
        ".task-navigation a[href], #sidebarNav nav a[href]"
    ))
        .filter((link) => {
            try {
                const url = new URL(link.href, window.location.origin);
                return url.origin === window.location.origin;
            } catch {
                return false;
            }
        });

    links.forEach((link) => {
        link.classList.remove("active", "task-nav-active");
        link.removeAttribute("aria-current");
    });

    const candidates = links
        .map((link) => ({
            link,
            path: new URL(link.href, window.location.origin).pathname.replace(/\/+$/, "") || "/",
        }))
        .filter(({ path }) => path !== "/" && (currentPath === path || currentPath.startsWith(`${path}/`)))
        .sort((a, b) => b.path.length - a.path.length);

    if (candidates.length) {
        candidates[0].link.classList.add("active", "task-nav-active");
        candidates[0].link.setAttribute("aria-current", "page");
    }
})();
