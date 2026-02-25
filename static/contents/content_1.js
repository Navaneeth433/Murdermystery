// Example frontend-only content logic for content 1.
// Real content should stay on the frontend; nothing about this challenge
// is stored in the database.

(function () {
  const root = document.getElementById("content-root");
  if (!root) return;

  const wrapper = document.createElement("div");
  wrapper.className = "card";
  wrapper.innerHTML = `
    <div class="card-body">
      <h5 class="card-title">Sample Puzzle</h5>
      <p class="card-text">
        Simple example: enter the secret word <code>flask</code> to complete this challenge.
      </p>
      <div class="mb-3">
        <input type="text" id="puzzle-answer" class="form-control" placeholder="Type the secret word" />
      </div>
      <div id="puzzle-feedback" class="small text-muted"></div>
    </div>
  `;
  root.appendChild(wrapper);

  const input = document.getElementById("puzzle-answer");
  const feedback = document.getElementById("puzzle-feedback");
  if (!input || !feedback) return;

  input.addEventListener("input", () => {
    if (input.value.trim().toLowerCase() === "flask") {
      feedback.textContent = "Looks correct! Now submit as Completed to record your score.";
      feedback.className = "small text-success";
    } else {
      feedback.textContent = "Not quite there yet.";
      feedback.className = "small text-muted";
    }
  });
})();



