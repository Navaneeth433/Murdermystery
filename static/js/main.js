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

  function attachContentHandlers() {
    const container = document.getElementById("content-container");
    if (!container) return;

    const contentId = container.getAttribute("data-content-id");
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
              ${completed ? "✔ File sealed. Chapter complete!" : "✘ File abandoned."}
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




