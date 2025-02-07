document.addEventListener("DOMContentLoaded", function() {

  const loadMoreBtn = document.getElementById("load-more");
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", function(event) {
        event.preventDefault();
        const nextPage = loadMoreBtn.getAttribute("data-next-page");

        // Get current URL and add/modify the page parameter.
        const url = new URL(window.location.href);
        url.searchParams.set("page", nextPage);
        
        // Optionally, preserve any filter parameter if present.
        // (If you have ?filter=... already, this will retain it.)

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
            document.getElementById("task-container").insertAdjacentHTML("beforeend", newTasksHTML);

            // Update or remove the Load More button.
            const newLoadMoreBtn = doc.getElementById("load-more");
            if (newLoadMoreBtn) {
                // Update the data attribute for the next page.
                loadMoreBtn.setAttribute("data-next-page", newLoadMoreBtn.getAttribute("data-next-page"));
            } else {
                // If no new load-more button exists, hide the current one.
                loadMoreBtn.style.display = "none";
            }
            })
            .catch(error => console.error("Error loading more tasks:", error));
        });
    }
  });