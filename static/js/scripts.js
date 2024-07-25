/*!
 * Start Bootstrap - Clean Blog v6.0.9 (https://startbootstrap.com/theme/clean-blog)
 * Copyright 2013-2023 Start Bootstrap
 * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-clean-blog/blob/master/LICENSE)
 */

window.addEventListener("DOMContentLoaded", () => {
  let scrollPos = 0;
  const mainNav = document.getElementById("mainNav");
  const headerHeight = mainNav.clientHeight;
  window.addEventListener("scroll", function () {
    const currentTop = document.body.getBoundingClientRect().top * -1;
    if (currentTop < scrollPos) {
      if (currentTop > 0 && mainNav.classList.contains("is-fixed")) {
        mainNav.classList.add("is-visible");
      } else {
        mainNav.classList.remove("is-visible", "is-fixed");
      }
    } else {
      mainNav.classList.remove(["is-visible"]);
      if (
        currentTop > headerHeight &&
        !mainNav.classList.contains("is-fixed")
      ) {
        mainNav.classList.add("is-fixed");
      }
    }
    scrollPos = currentTop;
  });

  let form = document.getElementById("myForm");

  if (form) {
    form.addEventListener("submit", function (event) {
      let confirmMessage = "Are you sure you want to proceed?";

      if (form.action.includes("edit-post")) {
        confirmMessage = "Are you sure you want to update this post?";
      }
      if (form.action.includes("new-post")) {
        confirmMessage = "Are you sure you want to add this post?";
      }
      if (form.action.includes("edit-comment")) {
        confirmMessage = "Are you sure you want to update this comment?";
      }
      if (form.action.includes("edit-rating")) {
        confirmMessage = "Are you sure you want to update this rating?";
      }
      if (!confirm(confirmMessage)) {
        event.preventDefault();
      }
    });
  }

  const execLinks = document.querySelectorAll(".exec-tag");

  if (execLinks) {
    execLinks.forEach((link) => {
      link.addEventListener("click", function (event) {
        event.preventDefault();

        let confirmMessage = "Are you sure you want to delete this item?";

        if (/\/delete-comment\//.test(this.href)) {
          confirmMessage = "Are you sure you want to delete this comment?";
        }

        if (/\/delete\//.test(this.href)) {
          confirmMessage = "Are you sure you want to delete this post?";
        }

        if (/\/process-posting\//.test(this.href)) {
          confirmMessage =
            "Are you sure you want to proceed with this permission?";
        }

        if (confirm(confirmMessage)) {
          window.location.href = this.href;
        }
      });
    });
  }

  const deleteForms = document.querySelectorAll(".delete-form");

  if (deleteForms) {
    deleteForms.forEach((form) => {
      form.addEventListener("submit", function (event) {
        event.preventDefault();

        let confirmMessage = "Are you sure you want to delete this item?";

        if (form.classList.contains("comment-form")) {
          confirmMessage = "Are you sure you want to delete this comment?";
        }
        if (form.classList.contains("rating-form")) {
          confirmMessage = "Are you sure you want to delete this rating?";
        }

        if (confirm(confirmMessage)) {
          event.target.submit();
        }
      });
    });
  }
});

var currentYear = new Date().getFullYear();
document.getElementById("currentYear").innerText = currentYear;
