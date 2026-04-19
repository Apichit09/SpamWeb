document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.getElementById("message");
  const charCount = document.getElementById("char-count");
  const clearBtn = document.getElementById("clear-btn");

  if (textarea && charCount) {
    const updateCount = () => {
      charCount.textContent = textarea.value.length;
    };

    textarea.addEventListener("input", updateCount);
    updateCount();
  }

  if (textarea && clearBtn) {
    clearBtn.addEventListener("click", () => {
      setTimeout(() => {
        if (charCount) charCount.textContent = "0";
      }, 0);
    });
  }
});