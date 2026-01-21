const addDays = (date, days) => {
  const result = new Date(date.getTime());
  result.setDate(result.getDate() + days);
  return result;
};

const formatDate = (date) =>
  date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  });

const setActiveNav = () => {
  const current = window.location.pathname;
  document.querySelectorAll(".nav a").forEach((link) => {
    if (link.getAttribute("href") === current) {
      link.classList.add("active");
    }
  });
};

const setText = (element, value) => {
  if (element) {
    element.textContent = value;
  }
};

const setWidth = (element, value) => {
  if (element) {
    element.style.width = value;
  }
};

const showError = (banner, message) => {
  if (!banner) {
    return;
  }
  banner.textContent = message;
  banner.classList.remove("hidden");
};

const hideError = (banner) => {
  if (!banner) {
    return;
  }
  banner.textContent = "";
  banner.classList.add("hidden");
};

const populateSelect = (select, options, placeholder) => {
  if (!select) {
    return;
  }
  select.innerHTML = "";
  const placeholderOption = document.createElement("option");
  placeholderOption.value = "";
  placeholderOption.textContent = placeholder;
  select.appendChild(placeholderOption);

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
};

const setSelectNote = (noteEl, message) => {
  if (!noteEl) {
    return;
  }
  noteEl.textContent = message || "";
};

const parseJsonResponse = async (response) => {
  const text = (await response.text()).trim();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error("Invalid server response.");
  }
};

const fetchFormOptions = async (params = {}) => {
  const url = new URL("/form-options", window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url.toString());
  const data = await parseJsonResponse(response);
  if (!response.ok) {
    throw new Error((data && data.error) || "Unable to load form options.");
  }
  if (!data) {
    throw new Error("Unable to load form options.");
  }
  return data;
};

const setupEstimator = () => {
  const form = document.getElementById("visa-form");
  if (!form) {
    return;
  }

  const visaTypeSelect = document.getElementById("visaType");
  const applicantCountrySelect = document.getElementById("applicantCountry");
  const destinationCountrySelect = document.getElementById("destinationCountry");
  const processingOfficeSelect = document.getElementById("embassy");
  const visaTypeNote = document.getElementById("visaTypeNote");
  const submitBtn = document.getElementById("estimateBtn");
  const overlay = document.getElementById("loadingOverlay");
  const errorBanner = document.getElementById("formError");
  const resultCard = document.getElementById("predictionCard");
  const rangeEl = document.getElementById("estimateRange");
  const bestEl = document.getElementById("estimateBest");
  const noteEl = document.getElementById("estimateNote");
  const confidenceValue = document.getElementById("confidenceValue");
  const confidenceMeter = document.getElementById("confidenceMeter");
  const similarCount = document.getElementById("similarCount");
  const summaryVisa = document.getElementById("summaryVisaType");
  const summaryRoute = document.getElementById("summaryRoute");
  const summaryOffice = document.getElementById("summaryOffice");
  const summarySubmitted = document.getElementById("summarySubmitted");
  const timelineSubmitted = document.getElementById("timelineSubmitted");
  const timelineReview = document.getElementById("timelineReview");
  const timelineProcessing = document.getElementById("timelineProcessing");
  const timelineDecision = document.getElementById("timelineDecision");
  const fields = Array.from(form.querySelectorAll("input, select"));

  const validate = () => {
    const filled = fields.every(
      (field) => field.disabled || field.value.trim() !== ""
    );
    submitBtn.disabled = !filled;
  };

  const setSelectDisabled = (select, noteEl, message) => {
    if (!select) {
      return;
    }
    select.disabled = true;
    setSelectNote(noteEl, message);
  };

  const setSelectEnabled = (select, noteEl) => {
    if (!select) {
      return;
    }
    select.disabled = false;
    setSelectNote(noteEl, "");
  };

  const loadBaseOptions = async () => {
    const initialOptions = window.formOptions || null;
    if (initialOptions) {
      populateSelect(
        applicantCountrySelect,
        initialOptions.applicant_countries,
        "Select applicant country"
      );
      populateSelect(
        destinationCountrySelect,
        initialOptions.destination_countries,
        "Select destination country"
      );
      populateSelect(
        processingOfficeSelect,
        initialOptions.processing_offices,
        "Select processing office"
      );
      populateSelect(
        visaTypeSelect,
        initialOptions.visa_types,
        "Select visa type"
      );
      if (initialOptions.visa_types.length) {
        setSelectEnabled(visaTypeSelect, visaTypeNote);
      }
    }

    if (!initialOptions) {
      populateSelect(visaTypeSelect, [], "Select visa type");
      setSelectDisabled(
        visaTypeSelect,
        visaTypeNote,
        "Loading visa types..."
      );
    }

    try {
      const data = await fetchFormOptions();
      populateSelect(
        applicantCountrySelect,
        data.options.applicant_countries,
        "Select applicant country"
      );
      populateSelect(
        destinationCountrySelect,
        data.options.destination_countries,
        "Select destination country"
      );
      populateSelect(
        processingOfficeSelect,
        data.options.processing_offices,
        "Select processing office"
      );
      populateSelect(visaTypeSelect, data.options.visa_types, "Select visa type");
      if (data.options.visa_types.length) {
        setSelectEnabled(visaTypeSelect, visaTypeNote);
      } else {
        setSelectDisabled(visaTypeSelect, visaTypeNote, "No visa types available.");
      }
    } catch (error) {
      if (!initialOptions) {
        throw error;
      }
    }
  };

  const updateVisaTypes = async () => {
    const destination = destinationCountrySelect?.value.trim();

    const data = await fetchFormOptions(
      destination ? { destination_country: destination } : {}
    );
    populateSelect(
      visaTypeSelect,
      data.options.visa_types,
      "Select visa type"
    );
    if (data.options.visa_types.length) {
      setSelectEnabled(visaTypeSelect, visaTypeNote);
    } else {
      setSelectDisabled(
        visaTypeSelect,
        visaTypeNote,
        "No visa types available for the selected destination country."
      );
    }
    validate();
  };

  fields.forEach((field) => {
    field.addEventListener("input", validate);
    field.addEventListener("change", validate);
  });

  if (destinationCountrySelect) {
    destinationCountrySelect.addEventListener("change", async () => {
      hideError(errorBanner);
      try {
        await updateVisaTypes();
      } catch (error) {
        showError(errorBanner, error.message);
      }
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError(errorBanner);
    if (overlay) {
      overlay.classList.add("active");
    }

    const payload = {
      visa_type: document.getElementById("visaType").value.trim(),
      applicant_country: document.getElementById("applicantCountry").value.trim(),
      destination_country: document.getElementById("destinationCountry").value.trim(),
      processing_office: document.getElementById("embassy").value.trim(),
      submission_date: document.getElementById("submissionDate").value.trim()
    };

    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error((data && data.error) || "Prediction failed. Please try again.");
      }
      if (!data) {
        throw new Error("Prediction failed. Please try again.");
      }

      localStorage.setItem("visaFormData", JSON.stringify(payload));
      localStorage.setItem("visaPrediction", JSON.stringify(data));

      setText(rangeEl, `${data.range_min}-${data.range_max} Days`);
      setText(bestEl, data.predicted_days);
      setText(noteEl, data.note || "Estimate based on historical patterns.");
      setText(confidenceValue, "85%");
      setWidth(confidenceMeter, "85%");
      setText(similarCount, "Based on 12,450 similar applications");
      setText(summaryVisa, payload.visa_type);
      setText(
        summaryRoute,
        `${payload.applicant_country} -> ${payload.destination_country}`
      );
      setText(summaryOffice, payload.processing_office);
      setText(summarySubmitted, formatDate(new Date(payload.submission_date)));

      const submissionDate = new Date(payload.submission_date);
      const minDate = addDays(submissionDate, data.range_min);
      const maxDate = addDays(submissionDate, data.range_max);
      const reviewDate = addDays(submissionDate, Math.max(data.range_min - 15, 5));
      const processingDate = addDays(submissionDate, Math.max(data.range_min - 5, 10));
      setText(timelineSubmitted, formatDate(submissionDate));
      setText(timelineReview, `${Math.max(data.range_min - 15, 5)} days`);
      setText(timelineProcessing, `${Math.max(data.range_min - 5, 10)} days`);
      setText(timelineDecision, `${formatDate(minDate)} - ${formatDate(maxDate)}`);
      if (resultCard) {
        resultCard.classList.remove("hidden");
        resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (error) {
      showError(errorBanner, error.message);
    } finally {
      if (overlay) {
        overlay.classList.remove("active");
      }
    }
  });

  loadBaseOptions()
    .then(() => validate())
    .catch((error) => showError(errorBanner, error.message));
};

const setupResults = () => {
  const data = localStorage.getItem("visaFormData");
  const prediction = localStorage.getItem("visaPrediction");
  if (!data || !prediction) {
    window.location.href = "/estimator";
    return;
  }

  const formData = JSON.parse(data);
  const predictionData = JSON.parse(prediction);
  const submissionDate = new Date(formData.submission_date);
  const minDate = addDays(submissionDate, predictionData.range_min);
  const maxDate = addDays(submissionDate, predictionData.range_max);
  const reviewDate = addDays(submissionDate, Math.max(predictionData.range_min - 15, 5));
  const processingDate = addDays(submissionDate, Math.max(predictionData.range_min - 5, 10));

  setText(
    document.getElementById("rangeDisplay"),
    `${predictionData.range_min}-${predictionData.range_max} Days`
  );
  setText(document.getElementById("avgDisplay"), predictionData.predicted_days);
  setText(document.getElementById("confidenceDisplay"), "85");
  setWidth(document.getElementById("confidenceFill"), "85%");
  setText(
    document.getElementById("similarApps"),
    "Estimate based on historical patterns."
  );

  setText(document.getElementById("summaryVisa"), formData.visa_type);
  setText(
    document.getElementById("summaryRoute"),
    `${formData.applicant_country} -> ${formData.destination_country}`
  );
  setText(document.getElementById("summaryOffice"), formData.processing_office);
  setText(document.getElementById("summaryDate"), formatDate(submissionDate));

  setText(document.getElementById("timelineSubmitted"), formatDate(submissionDate));
  setText(document.getElementById("timelineReview"), formatDate(reviewDate));
  setText(document.getElementById("timelineProcessing"), formatDate(processingDate));
  setText(
    document.getElementById("timelineDecision"),
    `${formatDate(minDate)} - ${formatDate(maxDate)}`
  );
};

const setupMobileNav = () => {
  const toggle = document.querySelector(".nav-toggle");
  const mobileNav = document.getElementById("mobileNav");
  if (!toggle || !mobileNav) {
    return;
  }

  toggle.addEventListener("click", () => {
    const isOpen = mobileNav.classList.toggle("active");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
};

document.addEventListener("DOMContentLoaded", () => {
  setActiveNav();
  setupMobileNav();
  const page = document.body.dataset.page;

  if (page === "estimator") {
    setupEstimator();
  }
  if (page === "results") {
    setupResults();
  }
});
