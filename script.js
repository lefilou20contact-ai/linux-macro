/* =====================================================
   FILOU MACRO SYSTEM
   V1 - RESEAU LOCAL
===================================================== */


let agentUrl = "";

let deviceConnected = false;

let macros = [];

let editingMacroId = null;


/* =====================================================
   OUTILS
===================================================== */

function $(id) {

    return document.getElementById(id);

}


function escapeHtml(value) {

    return String(value ?? "")
        .replace(/[&<>"']/g, char => {

            const map = {

                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"

            };

            return map[char];

        });

}


function showToast(message) {

    const toast = $("toast");

    toast.textContent = message;

    toast.style.display = "block";

    clearTimeout(window.toastTimer);

    window.toastTimer =
        setTimeout(() => {

            toast.style.display =
                "none";

        }, 2500);

}


/* =====================================================
   CONNEXION
===================================================== */

function loadConnection() {

    try {

        const saved =
            localStorage.getItem(
                "filou_connection_v1"
            );


        if (!saved) {

            return;

        }


        const data =
            JSON.parse(saved);


        $("deviceName").value =
            data.name || "";


        $("deviceCode").value =
            data.code || "";


        $("deviceAddress").value =
            data.address || "";

    }

    catch {

        console.error(
            "Impossible de charger la connexion."
        );

    }

}


function saveConnection() {

    const name =
        $("deviceName")
            .value
            .trim();


    const code =
        $("deviceCode")
            .value
            .trim();


    const address =
        $("deviceAddress")
            .value
            .trim();


    if (!name) {

        showConnectionMessage(
            "Entre le nom de l'appareil.",
            false
        );

        return;

    }


    if (!code) {

        showConnectionMessage(
            "Entre le code de l'appareil.",
            false
        );

        return;

    }


    if (!address) {

        showConnectionMessage(
            "Entre l'adresse locale du PC.",
            false
        );

        return;

    }


    localStorage.setItem(

        "filou_connection_v1",

        JSON.stringify({

            name,
            code,
            address

        })

    );


    showConnectionMessage(
        "✓ Connexion enregistrée.",
        true
    );

}


function showConnectionMessage(
    message,
    success
) {

    const element =
        $("connectionMessage");


    element.textContent =
        message;


    element.className =
        success
            ? "message success"
            : "message error";

}


/* =====================================================
   URL AGENT
===================================================== */

function getAgentUrl() {

    let address =
        $("deviceAddress")
            .value
            .trim();


    if (!address) {

        return "";

    }


    if (
        !address.startsWith("http://") &&
        !address.startsWith("https://")
    ) {

        address =
            "http://" +
            address;

    }


    return address.replace(
        /\/$/,
        ""
    );

}


/* =====================================================
   CONNECTER
===================================================== */

async function connectToAgent() {

    const name =
        $("deviceName")
            .value
            .trim();


    const code =
        $("deviceCode")
            .value
            .trim();


    agentUrl =
        getAgentUrl();


    if (!name || !code || !agentUrl) {

        showConnectionMessage(
            "Remplis les trois champs.",
            false
        );

        return;

    }


    try {

        const response =
            await fetch(
                agentUrl +
                "/api/connect",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            name,
                            code

                        })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Connexion refusée."
            );

        }


        deviceConnected =
            true;


        localStorage.setItem(

            "filou_connection_v1",

            JSON.stringify({

                name,
                code,
                address:
                    $("deviceAddress")
                        .value
                        .trim()

            })

        );


        $("statusDot")
            .className =
            "status-dot online";


        $("statusText")
            .textContent =
            "Connecté";


        $("displayDevice")
            .textContent =
            name;


        $("displayAddress")
            .textContent =
            agentUrl;


        showConnectionMessage(
            "✓ Appareil connecté.",
            true
        );


        await loadMacros();


    }

    catch (error) {

        deviceConnected =
            false;


        $("statusDot")
            .className =
            "status-dot offline";


        $("statusText")
            .textContent =
            "Déconnecté";


        showConnectionMessage(

            "❌ " +
            (
                error.message ||
                "Impossible de joindre l'appareil."
            ),

            false

        );

    }

}


/* =====================================================
   MACROS
===================================================== */

async function loadMacros() {

    if (!agentUrl) {

        renderMacros();

        return;

    }


    try {

        const response =
            await fetch(

                agentUrl +
                "/api/macros",

                {
                    cache:
                        "no-store"
                }

            );


        if (!response.ok) {

            throw new Error();

        }


        const data =
            await response.json();


        if (Array.isArray(data)) {

            macros = data;

            renderMacros();

        }

    }

    catch {

        renderMacros();

    }

}


/* =====================================================
   NOM DES ACTIONS
===================================================== */

function actionName(type) {

    const names = {

        open_app:
            "🚀 Ouvrir une application",

        open_file:
            "📂 Ouvrir un fichier",

        open_url:
            "🌐 Ouvrir une URL",

        command:
            "💻 Exécuter une commande",

        text:
            "⌨️ Écrire du texte",

        key:
            "🎹 Appuyer sur une touche",

        wait:
            "⏱️ Attendre",

        mouse:
            "🖱️ Action souris"

    };


    return names[type] || type;

}


/* =====================================================
   CREER UNE ACTION
===================================================== */

function createActionElement(
    action,
    index
) {

    const element =
        document.createElement(
            "div"
        );


    element.className =
        "action";


    element.dataset.type =
        action.type;


    let fields = "";


    if (
        action.type ===
        "open_app"
    ) {

        fields = `

            <input
                data-field="value"
                value="${escapeHtml(action.value || "")}"
                placeholder="Ex : firefox"
            >

        `;

    }


    else if (
        action.type ===
        "open_file"
    ) {

        fields = `

            <input
                data-field="value"
                value="${escapeHtml(action.value || "")}"
                placeholder="Ex : ~/Documents/test.txt"
            >

        `;

    }


    else if (
        action.type ===
        "open_url"
    ) {

        fields = `

            <input
                data-field="value"
                value="${escapeHtml(action.value || "")}"
                placeholder="https://..."
            >

        `;

    }


    else if (
        action.type ===
        "command"
    ) {

        fields = `

            <input
                data-field="value"
                value="${escapeHtml(action.value || "")}"
                placeholder="Commande Linux"
            >

            <label>

                <input
                    data-field="approved"
                    type="checkbox"
                    ${action.approved ? "checked" : ""}
                >

                Je confirme cette commande

            </label>

        `;

    }


    else if (
        action.type ===
        "text"
    ) {

        fields = `

            <textarea
                data-field="value"
                rows="3"
                placeholder="Texte à écrire..."
            >${escapeHtml(action.value || "")}</textarea>

        `;

    }


    else if (
        action.type ===
        "key"
    ) {

        fields = `

            <input
                data-field="value"
                value="${escapeHtml(action.value || "")}"
                placeholder="Ex : F3, F2, CTRL+S"
            >

        `;

    }


    else if (
        action.type ===
        "wait"
    ) {

        fields = `

            <input
                data-field="ms"
                type="number"
                min="0"
                value="${action.ms || 500}"
            >

        `;

    }


    else if (
        action.type ===
        "mouse"
    ) {

        fields = `

            <select data-field="value">

                <option
                    value="left_click"
                    ${action.value === "left_click" ? "selected" : ""}
                >
                    Clic gauche
                </option>

                <option
                    value="right_click"
                    ${action.value === "right_click" ? "selected" : ""}
                >
                    Clic droit
                </option>

                <option
                    value="double_click"
                    ${action.value === "double_click" ? "selected" : ""}
                >
                    Double-clic
                </option>

            </select>

        `;

    }


    element.innerHTML = `

        <div class="action-header">

            <span class="action-title">
                ${actionName(action.type)}
            </span>

            <button
                class="button danger"
                data-remove="${index}"
            >
                🗑️ Supprimer
            </button>

        </div>

        <div class="action-fields">

            ${fields}

        </div>

    `;


    return element;

}


/* =====================================================
   AFFICHER LES ACTIONS
===================================================== */

function renderBuilder(
    actions = []
) {

    const list =
        $("actionList");


    list.innerHTML = "";


    actions.forEach(
        (action, index) => {

            list.appendChild(

                createActionElement(
                    action,
                    index
                )

            );

        }
    );


    list
        .querySelectorAll(
            "[data-remove]"
        )
        .forEach(button => {

            button.onclick = () => {

                button
                    .closest(".action")
                    .remove();

            };

        });

}


/* =====================================================
   RECUPERER LES ACTIONS
===================================================== */

function collectActions() {

    return [

        ...$("actionList").children

    ].map(element => {

        const type =
            element.dataset.type;


        const action = {

            type

        };


        if (
            type === "wait"
        ) {

            action.ms =
                Number(
                    element
                        .querySelector(
                            '[data-field="ms"]'
                        )
                        .value
                );

        }

        else {

            const field =
                element
                    .querySelector(
                        '[data-field="value"]'
                    );


            if (field) {

                action.value =
                    field.value;

            }


            if (
                type ===
                "command"
            ) {

                action.approved =
                    element
                        .querySelector(
                            '[data-field="approved"]'
                        )
                        .checked;

            }

        }


        return action;

    });

}


/* =====================================================
   AJOUTER ACTION
===================================================== */

$("addAction").onclick =
    () => {

        const type =
            $("actionType").value;


        if (!type) {

            return;

        }


        const actions =
            collectActions();


        actions.push({

            type

        });


        renderBuilder(
            actions
        );


        $("actionType").value =
            "";

    };


/* =====================================================
   ENREGISTRER MACRO
===================================================== */

$("saveMacro").onclick =
    async () => {

        const name =
            $("macroName")
                .value
                .trim();


        if (!name) {

            showToast(
                "❌ Donne un nom à la macro."
            );

            return;

        }


        const macro = {

            id:
                editingMacroId ||
                "macro-" +
                Date.now(),

            name,

            description:
                $("macroDescription")
                    .value
                    .trim(),

            actions:
                collectActions()

        };


        const index =
            macros.findIndex(
                item =>
                    item.id ===
                    macro.id
            );


        if (index >= 0) {

            macros[index] =
                macro;

        }

        else {

            macros.push(
                macro
            );

        }


        if (agentUrl) {

            try {

                const response =
                    await fetch(

                        agentUrl +
                        "/api/macros",

                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify(
                                    macros
                                )

                        }

                    );


                if (!response.ok) {

                    throw new Error();

                }

            }

            catch {

                showToast(
                    "⚠️ Macro conservée localement."
                );

            }

        }


        localStorage.setItem(

            "filou_macros_local_v1",

            JSON.stringify(
                macros
            )

        );


        renderMacros();

        resetBuilder();

        showToast(
            "✓ Macro enregistrée."
        );

    };


/* =====================================================
   AFFICHER MACROS
===================================================== */

function renderMacros() {

    const list =
        $("macroList");


    list.innerHTML = "";


    if (!macros.length) {

        list.innerHTML = `

            <div class="empty">

                Aucune macro.

            </div>

        `;

        return;

    }


    macros.forEach(
        macro => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "macro-card";


            card.innerHTML = `

                <h3>
                    ${escapeHtml(
                        macro.name
                    )}
                </h3>

                <p class="macro-description">

                    ${escapeHtml(
                        macro.description ||
                        "Aucune description."
                    )}

                </p>

                <p>
                    ${macro.actions.length}
                    action(s)
                </p>

                <div class="macro-actions">

                    <button
                        class="button primary"
                        data-run="${macro.id}"
                    >
                        ▶️ Exécuter
                    </button>

                    <button
                        class="button secondary"
                        data-edit="${macro.id}"
                    >
                        ✏️ Modifier
                    </button>

                    <button
                        class="button danger"
                        data-delete="${macro.id}"
                    >
                        🗑️ Supprimer
                    </button>

                </div>

            `;


            list.appendChild(
                card
            );

        }
    );


    list
        .querySelectorAll(
            "[data-run]"
        )
        .forEach(button => {

            button.onclick =
                () =>
                    runMacro(
                        button.dataset.run
                    );

        });


    list
        .querySelectorAll(
            "[data-edit]"
        )
        .forEach(button => {

            button.onclick =
                () =>
                    editMacro(
                        button.dataset.edit
                    );

        });


    list
        .querySelectorAll(
            "[data-delete]"
        )
        .forEach(button => {

            button.onclick =
                () =>
                    deleteMacro(
                        button.dataset.delete
                    );

        });

}


/* =====================================================
   EXECUTER
===================================================== */

async function runMacro(id) {

    if (!agentUrl) {

        showToast(
            "❌ Connecte d'abord ton appareil."
        );

        return;

    }


    try {

        const response =
            await fetch(

                agentUrl +
                "/api/run/" +
                encodeURIComponent(id),

                {

                    method:
                        "POST"

                }

            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Erreur d'exécution."
            );

        }


        showToast(
            "▶️ Macro exécutée."
        );

    }

    catch (error) {

        showToast(

            "❌ " +
            (
                error.message ||
                "Erreur."
            )

        );

    }

}


/* =====================================================
   MODIFIER
===================================================== */

function editMacro(id) {

    const macro =
        macros.find(
            item =>
                item.id === id
        );


    if (!macro) {

        return;

    }


    editingMacroId =
        macro.id;


    $("macroName").value =
        macro.name;


    $("macroDescription").value =
        macro.description || "";


    renderBuilder(
        macro.actions
    );


    $("saveMacro")
        .textContent =
        "💾 Enregistrer les modifications";


    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}


/* =====================================================
   SUPPRIMER
===================================================== */

async function deleteMacro(id) {

    if (
        !confirm(
            "Supprimer cette macro ?"
        )
    ) {

        return;

    }


    macros =
        macros.filter(
            item =>
                item.id !== id
        );


    localStorage.setItem(

        "filou_macros_local_v1",

        JSON.stringify(
            macros
        )

    );


    if (agentUrl) {

        try {

            await fetch(

                agentUrl +
                "/api/macros",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            macros
                        )

                }

            );

        }

        catch {}

    }


    renderMacros();

    showToast(
        "Macro supprimée."
    );

}


/* =====================================================
   RESET
===================================================== */

$("resetMacro").onclick =
    () => {

        editingMacroId =
            null;


        $("macroName").value =
            "";


        $("macroDescription").value =
            "";


        $("actionList")
            .innerHTML =
            "";


        $("saveMacro")
            .textContent =
            "💾 Enregistrer la macro";

    };


/* =====================================================
   EXPORT
===================================================== */

$("exportJson").onclick =
    () => {

        const json =
            JSON.stringify(
                macros,
                null,
                2
            );


        const blob =
            new Blob(
                [json],
                {
                    type:
                        "application/json"
                }
            );


        const url =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            url;


        link.download =
            "macros.json";


        link.click();


        URL.revokeObjectURL(
            url
        );

    };


/* =====================================================
   BOUTONS CONNEXION
===================================================== */

$("connectButton")
    .onclick =
    connectToAgent;


$("saveConnection")
    .onclick =
    saveConnection;


$("refreshMacros")
    .onclick =
    loadMacros;


/* =====================================================
   INITIALISATION
===================================================== */

loadConnection();


try {

    const local =
        localStorage.getItem(
            "filou_macros_local_v1"
        );


    if (local) {

        macros =
            JSON.parse(local);

    }

}

catch {}


renderMacros();
