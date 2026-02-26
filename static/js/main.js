window.ChallengeHost = (function () {

  /* ── Floating +N score animation ────────────────────────────────────────── */
  function showScoreFloat(points, label, delay) {
    delay = delay || 0;
    setTimeout(function () {
      var el = document.createElement("div");
      el.className = "score-float";
      el.textContent = "+" + points + (label ? " " + label : "");
      // Centre-ish of viewport
      el.style.left = "50%";
      el.style.top = "60%";
      el.style.transform = "translateX(-50%)";
      document.body.appendChild(el);
      el.addEventListener("animationend", function () { el.remove(); });
    }, delay);
  }

  /* ── Update nav score badges in-place ───────────────────────────────────── */
  function bumpNavScore(addedPoints) {
    ["nav-score-desktop", "nav-score-mobile"].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      var current = parseInt(el.textContent.replace(/\D/g, ""), 10) || 0;
      el.textContent = "\u2605 " + (current + addedPoints);
    });
  }

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

          var chPts = data.chapter_points || data.score || 0;
          var bonusPts = data.bonus_points || 0;
          var totalPts = data.total_points || (chPts + bonusPts);

          /* Build success message */
          var bonusLabel = "";
          if (bonusPts === 500) bonusLabel = " · 🥇 First to solve! <em>(+500 bonus)</em>";
          else if (bonusPts === 300) bonusLabel = " · 🥈 Second to solve! <em>(+300 bonus)</em>";
          else if (bonusPts === 150) bonusLabel = " · 🥉 Third to solve! <em>(+150 bonus)</em>";
          else if (bonusPts === 100) bonusLabel = " · <em>+100 placement bonus</em>";
          else if (bonusPts === 50) bonusLabel = " · <em>+50 placement bonus</em>";

          submitDiv.innerHTML = completed
            ? `<div class="alert alert-success">
                ✔ File sealed. Chapter complete! &nbsp;<strong>+${chPts} pts</strong> (base)${bonusLabel}
               </div>`
            : `<div class="alert alert-danger">✘ File abandoned.</div>`;

          /* Floating animations */
          if (completed && chPts > 0) {
            showScoreFloat(chPts, "pts", 0);
          }
          if (bonusPts > 0) {
            showScoreFloat(bonusPts, "bonus!", 700);
          }

          /* Update nav badge live */
          if (completed && totalPts > 0) {
            bumpNavScore(totalPts);
          }

          if (data.revealed) {
            setTimeout(function () {
              window.location.href = "/chapters?revealed=1";
            }, 1800);
          } else if (completed) {
            setTimeout(function () {
              window.location.href = "/chapters";
            }, 2200);
          }
        })
        .catch(() => {
          submitDiv.innerHTML = `<div class="alert alert-danger">Network error while submitting.</div>`;
        });
    }

    const btnCompleted = document.getElementById("btn-submit-completed");
    const btnIncomplete = document.getElementById("btn-submit-incomplete");
    if (btnCompleted) {
      btnCompleted.addEventListener("click", () => {
        const puzzleUrl = btnCompleted.getAttribute("data-puzzle-url");
        const quizUrl = btnCompleted.getAttribute("data-quiz-url");
        const callgameUrl = btnCompleted.getAttribute("data-callgame-url");
        const codegateUrl = btnCompleted.getAttribute("data-codegate-url");
        if (puzzleUrl) {
          window.location.href = puzzleUrl;
        } else if (quizUrl) {
          window.location.href = quizUrl;
        } else if (callgameUrl) {
          window.location.href = callgameUrl;
        } else if (codegateUrl) {
          window.location.href = codegateUrl;
        } else {
          submit(true);
        }
      });
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
