(function () {
    const normalize = (value) => value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase("vi");

    function enhanceSelect(select) {
        if (select.closest(".searchable-select")) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "searchable-select";
        wrapper.dataset.searchableSelect = "true";

        const input = document.createElement("input");
        input.type = "search";
        input.className = "searchable-select-input";
        input.autocomplete = "off";
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");
        input.setAttribute("aria-controls", `searchable-options-${Math.random().toString(36).slice(2)}`);
        input.setAttribute(
            "aria-label",
            select.name === "nha_cung_cap" ? "Tìm và chọn nhà cung cấp" : "Tìm và chọn sản phẩm",
        );
        input.placeholder = select.options[0]?.textContent.trim() || "Tìm kiếm...";
        input.required = select.required;

        const listbox = document.createElement("div");
        listbox.className = "searchable-select-listbox";
        listbox.id = input.getAttribute("aria-controls");
        listbox.setAttribute("role", "listbox");
        listbox.hidden = true;

        select.dataset.searchableRequired = String(select.required);
        select.required = false;
        select.classList.add("searchable-native-select");
        select.tabIndex = -1;
        select.parentNode.insertBefore(wrapper, select);
        wrapper.append(input, listbox, select);

        const getOptions = () => Array.from(select.options)
            .filter((option) => option.value && !option.disabled && !option.hidden);
        const selectedOption = () => select.options[select.selectedIndex];

        function syncInput() {
            const selected = selectedOption();
            input.value = selected?.value ? selected.textContent.trim().replace(/\s+/g, " ") : "";
            input.setCustomValidity(selected?.value ? "" : "Vui lòng chọn một mục trong danh sách.");
        }

        function close() {
            listbox.hidden = true;
            input.setAttribute("aria-expanded", "false");
            input.removeAttribute("aria-activedescendant");
        }

        function choose(option) {
            select.value = option.value;
            syncInput();
            close();
            select.dispatchEvent(new Event("change", { bubbles: true }));
        }

        function render(query = "") {
            const search = normalize(query.trim());
            const matches = getOptions().filter((option) =>
                normalize(option.textContent.trim()).includes(search),
            );
            listbox.replaceChildren();

            if (!matches.length) {
                const empty = document.createElement("div");
                empty.className = "searchable-select-empty";
                empty.textContent = "Không tìm thấy kết quả phù hợp.";
                listbox.appendChild(empty);
                return;
            }

            matches.forEach((option, index) => {
                const button = document.createElement("button");
                button.type = "button";
                button.id = `${listbox.id}-option-${index}`;
                button.className = "searchable-select-option";
                button.setAttribute("role", "option");
                button.setAttribute("aria-selected", String(option.value === select.value));
                button.dataset.optionValue = option.value;
                button.textContent = option.textContent.trim().replace(/\s+/g, " ");
                button.addEventListener("pointerdown", (event) => event.preventDefault());
                button.addEventListener("click", () => choose(option));
                listbox.appendChild(button);
            });
        }

        input.addEventListener("focus", () => {
            render(input.value);
            listbox.hidden = false;
            input.setAttribute("aria-expanded", "true");
        });

        input.addEventListener("input", () => {
            select.value = "";
            input.setCustomValidity("Vui lòng chọn một mục trong danh sách.");
            render(input.value);
            listbox.hidden = false;
            input.setAttribute("aria-expanded", "true");
        });

        select.addEventListener("optionschanged", () => {
            render(input.value);
            syncInput();
        });

        input.addEventListener("keydown", (event) => {
            const options = Array.from(listbox.querySelectorAll('[role="option"]'));
            const activeIndex = options.findIndex((option) => option.classList.contains("is-active"));

            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                event.preventDefault();
                listbox.hidden = false;
                input.setAttribute("aria-expanded", "true");
                const nextIndex = event.key === "ArrowDown"
                    ? Math.min(activeIndex + 1, options.length - 1)
                    : Math.max(activeIndex - 1, 0);
                options.forEach((option) => option.classList.remove("is-active"));
                if (options[nextIndex]) {
                    options[nextIndex].classList.add("is-active");
                    input.setAttribute("aria-activedescendant", options[nextIndex].id);
                    options[nextIndex].scrollIntoView({ block: "nearest" });
                }
            } else if (event.key === "Enter" && !listbox.hidden) {
                const activeOption = options.find((option) => option.classList.contains("is-active"));
                if (activeOption) {
                    event.preventDefault();
                    const option = getOptions().find((item) => item.value === activeOption.dataset.optionValue);
                    if (option) choose(option);
                }
            } else if (event.key === "Escape") {
                close();
                syncInput();
            }
        });

        select.addEventListener("change", syncInput);
        syncInput();
    }

    function initialize(root = document) {
        root.querySelectorAll('select[name="nha_cung_cap"], select.select-hang').forEach(enhanceSelect);
    }

    function resetClonedSelects(root) {
        root.querySelectorAll(".searchable-select").forEach((wrapper) => {
            const select = wrapper.querySelector("select");
            if (!select) {
                return;
            }
            wrapper.replaceWith(select);
            select.classList.remove("searchable-native-select");
            select.removeAttribute("tabindex");
            select.required = select.dataset.searchableRequired === "true";
            select.selectedIndex = 0;
            Array.from(select.options).forEach((option) => option.removeAttribute("hidden"));
            delete select.dataset.searchableRequired;
        });
    }

    document.addEventListener("click", (event) => {
        document.querySelectorAll(".searchable-select").forEach((wrapper) => {
            if (!wrapper.contains(event.target)) {
                wrapper.querySelector(".searchable-select-input")?.setAttribute("aria-expanded", "false");
                const listbox = wrapper.querySelector(".searchable-select-listbox");
                if (listbox) {
                    listbox.hidden = true;
                }
            }
        });
    });

    window.initializeSearchableSelects = initialize;
    window.resetClonedSearchableSelects = resetClonedSelects;
    initialize();
})();
