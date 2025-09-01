document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("reviewModal");
    const openBtn = document.getElementById("openModalBtn");
    const closeBtn = document.querySelector(".close");
    const checkboxes = document.querySelectorAll("input[name='categories']");
    const ratingContainer = document.getElementById("ratingInputs");
    const commentBox = document.getElementById("text");
    const tagContainer = document.getElementById("tagContainer");
    const submitBtn = document.getElementById("submitReviewBtn");
    const customTagInput = document.getElementById("customTagInput");

    openBtn.onclick = () => modal.style.display = "block";
    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; }

    checkboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            ratingContainer.innerHTML = "";
            checkboxes.forEach(c => {
                if (c.checked) {
                    ratingContainer.innerHTML += `
                        <label>${c.value.charAt(0).toUpperCase() + c.value.slice(1)} Rating (1–10):</label>
                        <input type="number" name="${c.value}" min="1" max="10" required><br>
                    `;
                }
            });
        });
    });

    let debounceTimer;
    commentBox.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            tagContainer.innerHTML = "<em>Loading tags...</em>";
            fetch("/generate_tags", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: commentBox.value })
            })
            .then(res => res.json())
            .then(data => {
                tagContainer.innerHTML = "";
                data.tags.forEach(tag => {
                    const span = document.createElement("span");
                    span.textContent = `#${tag}`;
                    span.classList.add("tag");
                    span.onclick = () => span.remove();
                    tagContainer.appendChild(span);
                });
            });
        }, 1000);
    });
    submitBtn.addEventListener("click", async () => 
    {
        const user = document.getElementById("user").value.trim();
        const text = commentBox.value.trim();

        // Gather selected categories
        const selectedCategories = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        // Get ratings for each selected category
        const ratings = {};
        selectedCategories.forEach(cat => {
            const ratingInput = document.querySelector(`input[name='${cat}']`);
            ratings[cat] = ratingInput ? parseInt(ratingInput.value) || 0 : 0;
        });

        // Gather tags from the tag container
        const tags = Array.from(tagContainer.querySelectorAll(".tag"))
            .map(tagEl => tagEl.textContent.replace("#", "").trim());

        // Get current college name from URL
        const collegeName = window.location.pathname.split("/").pop();

        const payload = {
            user,
            text,
            tags,
            rated_categories: selectedCategories,  // ✅ send which categories were checked
            food: ratings["food"] ?? null,
            social: ratings["social"] ?? null,
            clubs: ratings["clubs"] ?? null,
            study: ratings["study"] ?? null,
            opportunities: ratings["opportunities"] ?? null
            };

        try {
                const res = await fetch(`/colleges/${collegeName}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    alert("✅ Review submitted!");
                    modal.style.display = "none";
                    location.reload();  // Optional: refresh to see new review
                } else {
                    alert("⚠️ Failed to submit review.");
                }
            } 
        catch (err) {
            console.error("❌ Submission error:", err);
            alert("Error submitting review.");
        }
    });

    customTagInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            const tagText = customTagInput.value.trim().replace(/^#/, "");
            if (tagText) {
                const span = document.createElement("span");
                span.textContent = `#${tagText}`;
                span.classList.add("tag");
                span.onclick = () => span.remove();
                tagContainer.appendChild(span);
                customTagInput.value = "";
            }
        }
    });
});

