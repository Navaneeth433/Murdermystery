window.ChallengeHost = (function () {
  function attachIndexHandlers() {
    const buttons = document.querySelectorAll(".btn-start-challenge");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const contentId = btn.getAttribute("data-content-id");
        if (!contentId) return;
        fetch(`/start/${contentId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        })
          .then((r) => r.json())
          .then((data) => {
            if (!data.ok) {
              if (data.error === "Exists") {
                // Allow re-entry to view the content if already attempted
                window.location.href = `/content/${contentId}`;
                return;
              }
              alert(data.error || "Unable to start challenge.");
              return;
            }
            window.location.href = `/content/${contentId}`;
          })
          .catch(() => {
            alert("Network error while starting challenge.");
          });
      });
    });
  }

  function formatSeconds(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function attachContentHandlers() {
    const container = document.getElementById("content-container");
    if (!container) return;

    const contentId = container.getAttribute("data-content-id");
    const timeLimit = parseInt(container.getAttribute("data-time-limit") || "0", 10);
    const timerValue = document.getElementById("timer-value");
    let remaining = timeLimit || 0;

    const submitDiv = document.getElementById("submit-result");

    function submit(completed) {
      fetch(`/submit/${contentId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ completed: !!completed }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (!data.ok) {
            submitDiv.innerHTML = `<div class="alert alert-danger">${data.error || "Submit failed."}</div>`;
            return;
          }
          submitDiv.innerHTML = `<div class="alert alert-success">
              Score: <strong>${data.score.toFixed(2)}</strong><br />
              Time taken (server): <strong>${data.time_taken}s</strong><br />
              Completed: <strong>${data.completed ? "Yes" : "No"}</strong>
            </div>`;
          if (data.revealed) {
            setTimeout(function () {
              window.location.href = "/chapters?revealed=1";
            }, 1500);
          }
        })
        .catch(() => {
          submitDiv.innerHTML = `<div class="alert alert-danger">Network error while submitting.</div>`;
        });
    }

    const btnCompleted = document.getElementById("btn-submit-completed");
    const btnIncomplete = document.getElementById("btn-submit-incomplete");
    if (btnCompleted) {
      btnCompleted.addEventListener("click", () => submit(true));
    }
    if (btnIncomplete) {
      btnIncomplete.addEventListener("click", () => submit(false));
    }
  }

  return {
    attachIndexHandlers,
    attachContentHandlers,
  };
})();



