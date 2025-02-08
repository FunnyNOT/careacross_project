document.addEventListener("DOMContentLoaded", function () {

    const loadMoreBtn = document.getElementById("load-more");
    const taskContainer = document.getElementById("task-container");

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", function (event) {
            event.preventDefault();
            const nextPage = loadMoreBtn.getAttribute("data-next-page");

            // Get current URL and add/modify the page parameter.
            const url = new URL(window.location.href);
            url.searchParams.set("page", nextPage);

            fetch(url)
                .then(response => response.text())
                .then(html => {
                    // Create a temporary DOM element to parse the fetched HTML.
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");

                    // Extract the tasks from the fetched content.
                    const newTasksContainer = doc.getElementById("task-container");
                    const newTasksHTML = newTasksContainer.innerHTML;

                    // Append the new tasks to the current task container.
                    taskContainer.insertAdjacentHTML("beforeend", newTasksHTML);

                    // Update or remove the Load More button.
                    const newLoadMoreBtn = doc.getElementById("load-more");
                    if (newLoadMoreBtn) {
                        loadMoreBtn.setAttribute("data-next-page", newLoadMoreBtn.getAttribute("data-next-page"));
                    } else {
                        loadMoreBtn.style.display = "none";
                    }
                })
                .catch(error => console.error("Error loading more tasks:", error));
        });
    }

    // Attach event listener using event delegation
    taskContainer.addEventListener("click", function (event) {
        const checkbox = event.target.closest(".check");

        if (checkbox) {
            let todoId = checkbox.getAttribute("data-todo-id");

            fetch("/toggle-todo/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify({ todo_id: todoId }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    checkbox.classList.toggle("completed");
                    checkbox.closest(".task").querySelector(".title").classList.toggle("completed");
                } else {
                    console.error("Error:", data.error);
                }
            })
            .catch(error => console.error("Request failed:", error));
        }
    });

});
