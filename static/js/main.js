/**
 * SkillSwap Client-Side Interactions
 * Clean vanilla JS for tabs, modals, dynamic filtering, and notification dismissals.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Auto-dismiss Flash Messages after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-8px)";
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // 2. Dashboard View Switcher (Creator View <-> Client View)
  const creatorTabBtn = document.getElementById("tab-creator-btn");
  const clientTabBtn = document.getElementById("tab-client-btn");
  const creatorView = document.getElementById("creator-view-section");
  const clientView = document.getElementById("client-view-section");

  if (creatorTabBtn && clientTabBtn && creatorView && clientView) {
    creatorTabBtn.addEventListener("click", () => {
      creatorTabBtn.classList.add("active");
      clientTabBtn.classList.remove("active");
      creatorView.style.display = "block";
      clientView.style.display = "none";
    });

    clientTabBtn.addEventListener("click", () => {
      clientTabBtn.classList.add("active");
      creatorTabBtn.classList.remove("active");
      clientView.style.display = "block";
      creatorView.style.display = "none";
    });
  }

  // 3. Modal Handlers (Generic)
  const modalTriggers = document.querySelectorAll("[data-modal-target]");
  const modalClosers = document.querySelectorAll("[data-modal-close]");

  modalTriggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute("data-modal-target");
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add("active");
      }
    });
  });

  modalClosers.forEach((closer) => {
    closer.addEventListener("click", () => {
      const backdrop = closer.closest(".modal-backdrop");
      if (backdrop) {
        backdrop.classList.remove("active");
      }
    });
  });

  // Close modal when clicking on backdrop
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("active");
      }
    });
  });

  // 4. Live Search & Category Filtering on Marketplace
  const searchInput = document.getElementById("marketplace-search");
  const serviceCards = document.querySelectorAll(".service-card[data-category]");

  if (searchInput && serviceCards.length > 0) {
    searchInput.addEventListener("input", (e) => {
      const term = e.target.value.toLowerCase().trim();
      serviceCards.forEach((card) => {
        const title = (card.getAttribute("data-title") || "").toLowerCase();
        const creator = (card.getAttribute("data-creator") || "").toLowerCase();
        const desc = (card.getAttribute("data-desc") || "").toLowerCase();

        if (title.includes(term) || creator.includes(term) || desc.includes(term)) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  }
});

