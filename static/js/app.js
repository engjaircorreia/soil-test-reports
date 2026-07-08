const labels = {
  pt: {
    brand: "Ensaios",
    themeToggle: "Claro/Escuro",
    newTestTitle: "Novo ensaio",
    reviewTitle: "Revisão dos dados",
    modelSection: "Modelo",
    fileSection: "Arquivos do ensaio",
    detectedFilesTitle: "Classificação automática dos arquivos",
    proctorSection: "Proctor / dados comuns",
    cbrSection: "CBR",
    gradationSection: "Granulometria e limites",
    uploadButton: "Enviar e extrair",
    saveReviewButton: "Salvar revisão",
    generateButton: "Gerar planilha",
    filesHelp: "Envie até 3 imagens ou PDFs",
    removeFile: "Remover arquivo",
    test_type: "Tipo de ensaio:",
    expected_test_type: "Tipo esperado:",
    language: "Idioma do modelo:",
    proctor_interessado: "Interessado / contratante:",
    proctor_obra: "Obra:",
    proctor_energia: "Energia Proctor:",
    proctor_registro: "Registro nº:",
    proctor_estaca: "Local / furo / estaca:",
    proctor_profundidade: "Profundidade do furo:",
    proctor_data_ensaio: "Data do ensaio:",
    proctor_procedencia: "Procedência / rua:",
    proctor_cidade: "Cidade:",
    proctor_responsavel_tecnico: "Responsável técnico:",
    proctor_observacoes: "Observações:",
    cbr_registro: "Registro nº do CBR:",
    cbr_molde_numero: "Molde nº:",
    cbr_peso_molde: "Peso do molde (g):",
    cbr_volume_molde: "Volume do molde (cm³):",
    cbr_numero_camadas: "Número de camadas:",
    cbr_golpes_camada: "Golpes por camada:",
    cbr_peso_soquete: "Peso do soquete (g):",
    cbr_espessura_disco: "Espessura do disco espaçador:",
    cbr_altura_cilindro: "Altura do cilindro (mm):",
    cbr_constante_prensa: "Constante da prensa:",
    gran_empresa_executora: "Empresa executora:",
    gran_obra: "Obra:",
    gran_procedencia: "Procedência / rua:",
    gran_camada: "Camada:",
    gran_estaca: "Local / furo / estaca:",
    gran_lado: "Lado:",
    gran_profundidade: "Profundidade do furo:",
    gran_data_ensaio: "Data do ensaio:",
    gran_laboratorio: "Laboratório:",
    gran_operador: "Operador:",
    gran_laboratorista: "Laboratorista:",
    gran_registro: "Registro nº:",
    files: "Arquivos:",
    umidade_otima: "Umidade ótima (%):",
    densidade_maxima: "Densidade máxima (g/cm³):",
    cbr: "CBR (%):",
    expansao: "Expansão (%):",
    passante_10: "Passante #10 (%):",
    passante_40: "Passante #40 (%):",
    passante_200: "Passante #200 (%):",
    classificacao_trb: "Classificação TRB:",
    classificacao_sucs: "Classificação SUCS:",
    ll: "LL:",
    lp: "LP:",
    ip: "IP:",
    options: {
      test_type: {
        compactacao_cbr: "Proctor / CBR",
        granulometria: "Granulometria",
        ambos: "Ambos",
      },
      expected_test_type: {
        auto: "Detectar automaticamente",
        compactacao_cbr: "Proctor / CBR",
        granulometria: "Granulometria",
        ambos: "Ambos",
      },
      language: {
        pt: "Português",
        en: "English",
      },
      proctor_energia: {
        "INTERMEDIÁRIO": "Intermediário",
        NORMAL: "Normal",
        MODIFICADO: "Modificado",
      },
    },
  },
  en: {
    brand: "Lab Tests",
    themeToggle: "Light/Dark",
    newTestTitle: "New test",
    reviewTitle: "Data review",
    modelSection: "Template",
    fileSection: "Test files",
    detectedFilesTitle: "Automatic file classification",
    proctorSection: "Proctor / common data",
    cbrSection: "CBR",
    gradationSection: "Particle size distribution and Atterberg limits",
    uploadButton: "Upload and extract",
    saveReviewButton: "Save review",
    generateButton: "Generate workbook",
    filesHelp: "Upload up to 3 images or PDFs",
    removeFile: "Remove file",
    test_type: "Test type:",
    expected_test_type: "Expected test type:",
    language: "Template language:",
    proctor_interessado: "Client / requester:",
    proctor_obra: "Project:",
    proctor_energia: "Proctor energy:",
    proctor_registro: "Record no.:",
    proctor_estaca: "Location / borehole / station:",
    proctor_profundidade: "Borehole depth:",
    proctor_data_ensaio: "Test date:",
    proctor_procedencia: "Source / street:",
    proctor_cidade: "City:",
    proctor_responsavel_tecnico: "Engineer in charge:",
    proctor_observacoes: "Notes:",
    cbr_registro: "CBR record no.:",
    cbr_molde_numero: "Mold no.:",
    cbr_peso_molde: "Mold weight (g):",
    cbr_volume_molde: "Mold volume (cm³):",
    cbr_numero_camadas: "Number of layers:",
    cbr_golpes_camada: "Blows per layer:",
    cbr_peso_soquete: "Rammer weight (g):",
    cbr_espessura_disco: "Spacer disk thickness:",
    cbr_altura_cilindro: "Cylinder height (mm):",
    cbr_constante_prensa: "Press constant:",
    gran_empresa_executora: "Testing company:",
    gran_obra: "Project:",
    gran_procedencia: "Source / street:",
    gran_camada: "Layer:",
    gran_estaca: "Location / borehole / station:",
    gran_lado: "Side:",
    gran_profundidade: "Borehole depth:",
    gran_data_ensaio: "Test date:",
    gran_laboratorio: "Laboratory:",
    gran_operador: "Operator:",
    gran_laboratorista: "Lab technician:",
    gran_registro: "Record no.:",
    files: "Files:",
    umidade_otima: "Optimum water content (%):",
    densidade_maxima: "Maximum dry density (g/cm³):",
    cbr: "California bearing ratio - CBR (%):",
    expansao: "Linear swelling (%):",
    passante_10: "Passing #10 (%):",
    passante_40: "Passing #40 (%):",
    passante_200: "Passing #200 (%):",
    classificacao_trb: "TRB classification:",
    classificacao_sucs: "USCS classification:",
    ll: "LL:",
    lp: "PL:",
    ip: "PI:",
    options: {
      test_type: {
        compactacao_cbr: "Proctor / CBR",
        granulometria: "Particle size distribution",
        ambos: "Both",
      },
      expected_test_type: {
        auto: "Auto-detect",
        compactacao_cbr: "Proctor / CBR",
        granulometria: "Particle size distribution",
        ambos: "Both",
      },
      language: {
        pt: "Portuguese",
        en: "English",
      },
      proctor_energia: {
        "INTERMEDIÁRIO": "Intermediate",
        NORMAL: "Standard",
        MODIFICADO: "Modified",
      },
    },
  },
};

const blockApplicability = {
  proctor: ["compactacao_cbr", "ambos"],
  cbr: ["compactacao_cbr", "ambos"],
  granulometria: ["granulometria", "ambos"],
};

const requiredFields = new Set([
  "proctor_interessado",
  "proctor_obra",
  "proctor_energia",
  "proctor_estaca",
  "proctor_data_ensaio",
  "proctor_procedencia",
  "cbr_registro",
  "cbr_molde_numero",
  "cbr_peso_molde",
  "cbr_volume_molde",
  "cbr_numero_camadas",
  "cbr_golpes_camada",
  "cbr_peso_soquete",
  "cbr_espessura_disco",
  "cbr_altura_cilindro",
  "cbr_constante_prensa",
  "gran_empresa_executora",
  "gran_obra",
  "gran_procedencia",
  "gran_estaca",
  "gran_data_ensaio",
]);

function labelText(key, text) {
  if (!requiredFields.has(key)) return text;
  return text.endsWith(":") ? `${text.slice(0, -1)} *:` : `${text} *`;
}

function selectedLanguage() {
  return document.querySelector("#id_language")?.value || "pt";
}

function selectedTestType() {
  const select = document.querySelector("#id_test_type");
  const expectedSelect = document.querySelector("#id_expected_test_type");
  if (select) return select.value;
  return expectedSelect ? expectedSelect.value : "auto";
}

function applyLanguage() {
  const language = selectedLanguage();
  const dictionary = labels[language] || labels.pt;
  document.documentElement.lang = language === "en" ? "en" : "pt-br";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (dictionary[key]) element.textContent = dictionary[key];
  });

  Object.entries(dictionary).forEach(([key, text]) => {
    const label = document.querySelector(`label[for="id_${key}"]`);
    if (label) label.textContent = labelText(key, text);
  });

  const filesHelp = document.querySelector("#id_files_helptext, [data-files-help]");
  if (filesHelp) filesHelp.textContent = dictionary.filesHelp;

  Object.entries(dictionary.options || {}).forEach(([field, options]) => {
    const select = document.querySelector(`#id_${field}`);
    if (!select) return;
    Array.from(select.options).forEach((option) => {
      if (options[option.value]) option.textContent = options[option.value];
    });
  });
}

function applyTestTypeVisibility() {
  const testType = selectedTestType();
  document.querySelectorAll("[data-test-block]").forEach((section) => {
    const appliesTo = blockApplicability[section.dataset.testBlock] || [];
    const hidden = testType === "auto" || !appliesTo.includes(testType);
    section.hidden = hidden;
    section.querySelectorAll("input, select, textarea").forEach((control) => {
      control.disabled = hidden;
    });
  });
}

function setupTheme() {
  const button = document.querySelector("[data-theme-toggle]");
  const root = document.documentElement;
  const stored = localStorage.getItem("theme");
  if (stored) root.dataset.theme = stored;
  button?.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", root.dataset.theme);
  });
}

function setupFormControls() {
  document.querySelector("#id_language")?.addEventListener("change", applyLanguage);
  document.querySelector("#id_test_type")?.addEventListener("change", applyTestTypeVisibility);
  document.querySelector("#id_expected_test_type")?.addEventListener("change", applyTestTypeVisibility);
  applyLanguage();
  applyTestTypeVisibility();
}

function syncFileInput(input, files) {
  const transfer = new DataTransfer();
  files.forEach((file) => transfer.items.add(file));
  input.files = transfer.files;
}

function renderSelectedFiles(input, list, files) {
  const language = selectedLanguage();
  const dictionary = labels[language] || labels.pt;
  list.innerHTML = "";
  files.forEach((file, index) => {
    const item = document.createElement("li");
    item.className = "selected-file-item";

    const name = document.createElement("span");
    name.className = "selected-file-name";
    name.textContent = file.name;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "file-remove-button";
    remove.textContent = "x";
    remove.setAttribute("aria-label", `${dictionary.removeFile}: ${file.name}`);
    remove.addEventListener("click", () => {
      files.splice(index, 1);
      syncFileInput(input, files);
      renderSelectedFiles(input, list, files);
    });

    item.append(name, remove);
    list.appendChild(item);
  });
}

function setupFileList() {
  const input = document.querySelector("#id_files");
  const list = document.querySelector("[data-selected-files]");
  if (!input || !list) return;

  const files = [];
  input.addEventListener("change", () => {
    files.splice(0, files.length, ...Array.from(input.files));
    syncFileInput(input, files);
    renderSelectedFiles(input, list, files);
  });
  document.querySelector("#id_language")?.addEventListener("change", () => {
    renderSelectedFiles(input, list, files);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupTheme();
  setupFormControls();
  setupFileList();
});
