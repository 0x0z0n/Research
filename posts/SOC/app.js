"use strict";

/* ============================================================
   SOC KNOWLEDGE BASE
   APP.JS
============================================================ */

/* ============================================================
   GLOBAL STATE
============================================================ */

const App = {

    manifest: null,

    files: [],

    categories: {},

    currentFile: null,

    currentCategory: "all",

    searchQuery: "",

    favorites: [],

    recent: [],

    cache: {},

    settings: {},

    initialized: false

};

/* ============================================================
   DOM
============================================================ */

const UI = {

    sidebar: document.querySelector(".sidebar"),

    folderTree: document.getElementById("folderTree"),

    fileGrid: document.getElementById("fileGrid"),

    breadcrumbs: document.getElementById("breadcrumbs"),

    viewer: document.getElementById("viewer"),

    viewerTitle: document.getElementById("viewerTitle"),

    viewerPath: document.getElementById("viewerPath"),

    viewerContent: document.getElementById("viewerContent"),

    globalSearch: document.getElementById("globalSearch"),

    sidebarSearch: document.getElementById("sidebarSearch"),

    overlaySearch: document.getElementById("overlaySearch"),

    overlayResults: document.getElementById("overlayResults"),

    statFiles: document.getElementById("statFiles"),

    statCategories: document.getElementById("statCategories"),

    statMarkdown: document.getElementById("statMarkdown"),

    statHTML: document.getElementById("statHTML"),

    statKQL: document.getElementById("statKQL"),

    statTXT: document.getElementById("statTXT"),

    categoryContainer: document.getElementById("categoryContainer"),

    favoriteContainer: document.getElementById("favoriteContainer"),

    recentContainer: document.getElementById("recentContainer"),

    loadingScreen: document.getElementById("loadingScreen"),

    toast: document.getElementById("toast"),

    toastMessage: document.getElementById("toastMessage")

};

/* ============================================================
   UTILITIES
============================================================ */

const Util = {

    extension(path){

        return path.split(".").pop().toLowerCase();

    },

    title(path){

        const name = path.split("/").pop();

        return name.replace(/\.[^/.]+$/, "");

    },

    debounce(fn, delay){

        let timer;

        return (...args)=>{

            clearTimeout(timer);

            timer = setTimeout(()=>fn(...args), delay);

        };

    },

    escape(text){

        const div=document.createElement("div");

        div.textContent=text;

        return div.innerHTML;

    },

    toast(message){

        UI.toastMessage.textContent=message;

        UI.toast.classList.remove("hidden");

        setTimeout(()=>{

            UI.toast.classList.add("hidden");

        },2000);

    }

};

/* ============================================================
   STORAGE
============================================================ */

const Storage={

    load(){

        App.favorites=

            JSON.parse(localStorage.getItem("favorites")||"[]");

        App.recent=

            JSON.parse(localStorage.getItem("recent")||"[]");

        App.settings=

            JSON.parse(localStorage.getItem("settings")||"{}");

    },

    save(){

        localStorage.setItem(

            "favorites",

            JSON.stringify(App.favorites)

        );

        localStorage.setItem(

            "recent",

            JSON.stringify(App.recent)

        );

        localStorage.setItem(

            "settings",

            JSON.stringify(App.settings)

        );

    }

};

/* ============================================================
   INITIALIZE
============================================================ */

document.addEventListener(

    "DOMContentLoaded",

    initialize

);

async function initialize(){

    Storage.load();

    await loadManifest();

    buildStatistics();

    buildTree();

    renderFiles();

    renderCategories();

    renderFavorites();

    renderRecent();

    registerEvents();

    UI.loadingScreen.style.display="none";

    App.initialized=true;

}
/* ============================================================
   LOAD MANIFEST
============================================================ */

async function loadManifest(){

    try{

        const response=await fetch(

            APP_CONFIG.manifest

        );

        if(!response.ok){

            throw new Error(

                "Unable to load manifest.json"

            );

        }

        App.manifest=await response.json();

        normalizeManifest();

    }

    catch(error){

        console.error(error);

        Util.toast("Failed to load manifest");

    }

}

/* ============================================================
   NORMALIZE MANIFEST
============================================================ */

function normalizeManifest(){

    App.files=[];

    App.categories={};

    if(!App.manifest.categories){

        return;

    }

    Object.entries(

        App.manifest.categories

    ).forEach(

        ([category,list])=>{

            App.categories[category]=[];

            list.forEach(file=>{

                const item={

                    id:

                        crypto.randomUUID(),

                    title:

                        file.title ||

                        Util.title(file.path),

                    description:

                        file.description ||

                        "",

                    path:

                        file.path,

                    category:

                        category,

                    extension:

                        Util.extension(file.path),

                    favorite:false,

                    recent:false

                };

                App.files.push(item);

                App.categories[category].push(item);

            });

        }

    );

}

/* ============================================================
   BUILD STATISTICS
============================================================ */

function buildStatistics(){

    const stats={

        md:0,

        html:0,

        kql:0,

        txt:0

    };

    App.files.forEach(file=>{

        switch(file.extension){

            case "md":

                stats.md++;

                break;

            case "html":

                stats.html++;

                break;

            case "kql":

                stats.kql++;

                break;

            case "txt":

                stats.txt++;

                break;

        }

    });

    UI.statFiles.textContent=

        App.files.length;

    UI.statCategories.textContent=

        Object.keys(

            App.categories

        ).length;

    UI.statMarkdown.textContent=

        stats.md;

    UI.statHTML.textContent=

        stats.html;

    UI.statKQL.textContent=

        stats.kql;

    UI.statTXT.textContent=

        stats.txt;

    document.getElementById(

        "countMD"

    ).textContent=stats.md;

    document.getElementById(

        "countHTML"

    ).textContent=stats.html;

    document.getElementById(

        "countKQL"

    ).textContent=stats.kql;

    document.getElementById(

        "countTXT"

    ).textContent=stats.txt;

    document.getElementById(

        "footerFiles"

    ).textContent=

        App.files.length;

    document.getElementById(

        "footerCategories"

    ).textContent=

        Object.keys(

            App.categories

        ).length;

}

/* ============================================================
   FILTER FILES
============================================================ */

function filteredFiles(){

    let files=[...App.files];

    if(

        App.currentCategory!=="all"

    ){

        files=files.filter(

            file=>

            file.category===

            App.currentCategory

        );

    }

    if(

        App.searchQuery.trim()

    ){

        const query=

            App.searchQuery

            .toLowerCase();

        files=files.filter(file=>{

            return(

                file.title

                .toLowerCase()

                .includes(query)

                ||

                file.path

                .toLowerCase()

                .includes(query)

                ||

                file.description

                .toLowerCase()

                .includes(query)

                ||

                file.category

                .toLowerCase()

                .includes(query)

            );

        });

    }

    return files;

}
/* ============================================================
   RENDER FILES
============================================================ */

function renderFiles(){

    const files=filteredFiles();

    UI.fileGrid.innerHTML="";

    document.getElementById(

        "resultCount"

    ).textContent=

        `${files.length} Files`;

    document.getElementById(

        "statusResults"

    ).textContent=

        files.length;

    if(!files.length){

        document.getElementById(

            "emptyState"

        ).classList.remove("hidden");

        return;

    }

    document.getElementById(

        "emptyState"

    ).classList.add("hidden");

    files.forEach(file=>{

        UI.fileGrid.appendChild(

            createFileCard(file)

        );

    });

}

/* ============================================================
   CREATE FILE CARD
============================================================ */

function createFileCard(file){

    const template=document

        .getElementById(

            "fileCardTemplate"

        )

        .content

        .cloneNode(true);

    const card=

        template.querySelector(

            ".file-card"

        );

    const icon=

        card.querySelector(

            ".file-icon i"

        );

    const title=

        card.querySelector(

            ".file-title"

        );

    const path=

        card.querySelector(

            ".file-path"

        );

    const description=

        card.querySelector(

            ".file-description"

        );

    const tags=

        card.querySelector(

            ".file-tags"

        );

    const type=

        card.querySelector(

            ".file-type"

        );

    const category=

        card.querySelector(

            ".file-category"

        );

    const favorite=

        card.querySelector(

            ".favorite-button"

        );

    title.textContent=file.title;

    path.textContent=file.path;

    description.textContent=

        file.description ||

        "No description available.";

    type.textContent=

        file.extension.toUpperCase();

    category.textContent=

        file.category;

    icon.className=

        fileIcon(file.extension);

    if(

        App.favorites.includes(

            file.path

        )

    ){

        favorite.innerHTML=

            '<i class="fa-solid fa-star"></i>';

    }

    favorite.addEventListener(

        "click",

        e=>{

            e.stopPropagation();

            toggleFavorite(file);

        }

    );

    card.addEventListener(

        "click",

        ()=>{

            openFile(file);

        }

    );

    addTag(

        tags,

        file.extension

    );

    addTag(

        tags,

        file.category

    );

    return template;

}

/* ============================================================
   TAG
============================================================ */

function addTag(

    container,

    text

){

    const tag=document

        .getElementById(

            "tagTemplate"

        )

        .content

        .cloneNode(true);

    tag.querySelector(

        ".tag"

    ).textContent=text;

    container.appendChild(tag);

}

/* ============================================================
   ICONS
============================================================ */

function fileIcon(ext){

    switch(ext){

        case "md":

            return "fa-solid fa-book";

        case "html":

            return "fa-brands fa-html5";

        case "css":

            return "fa-brands fa-css3-alt";

        case "js":

            return "fa-brands fa-js";

        case "kql":

            return "fa-solid fa-database";

        case "txt":

            return "fa-solid fa-file-lines";

        default:

            return "fa-solid fa-file";

    }

}

/* ============================================================
   CATEGORY LIST
============================================================ */

function renderCategories(){

    UI.categoryContainer.innerHTML="";

    Object.entries(

        App.categories

    ).forEach(

        ([name,list])=>{

            const template=document

                .getElementById(

                    "categoryTemplate"

                )

                .content

                .cloneNode(true);

            template.querySelector(

                ".category-name"

            ).textContent=name;

            template.querySelector(

                ".category-count"

            ).textContent=

                `${list.length} Files`;

            template.querySelector(

                ".category-card"

            ).onclick=()=>{

                App.currentCategory=name;

                renderFiles();

            };

            UI.categoryContainer

                .appendChild(template);

        }

    );

}

/* ============================================================
   FAVORITES
============================================================ */

function renderFavorites(){

    UI.favoriteContainer.innerHTML="";

    if(

        !App.favorites.length

    ){

        UI.favoriteContainer.appendChild(

            document

            .getElementById(

                "emptyFavoritesTemplate"

            )

            .content

            .cloneNode(true)

        );

        return;

    }

    App.favorites.forEach(path=>{

        const file=

            App.files.find(

                f=>f.path===path

            );

        if(!file) return;

        const template=document

            .getElementById(

                "favoriteTemplate"

            )

            .content

            .cloneNode(true);

        template.querySelector(

            "h4"

        ).textContent=file.title;

        template.querySelector(

            "small"

        ).textContent=file.path;

        template.querySelector(

            ".favorite-item"

        ).onclick=()=>{

            openFile(file);

        };

        UI.favoriteContainer

            .appendChild(template);

    });

}

/* ============================================================
   RECENT
============================================================ */

function renderRecent(){

    UI.recentContainer.innerHTML="";

    if(

        !App.recent.length

    ){

        UI.recentContainer.appendChild(

            document

            .getElementById(

                "emptyRecentTemplate"

            )

            .content

            .cloneNode(true)

        );

        return;

    }

    App.recent.forEach(path=>{

        const file=

            App.files.find(

                f=>f.path===path

            );

        if(!file) return;

        const template=document

            .getElementById(

                "recentTemplate"

            )

            .content

            .cloneNode(true);

        template.querySelector(

            "h4"

        ).textContent=file.title;

        template.querySelector(

            "small"

        ).textContent=file.path;

        template.querySelector(

            ".recent-item"

        ).onclick=()=>{

            openFile(file);

        };

        UI.recentContainer

            .appendChild(template);

    });

}
/* ============================================================
   BUILD FOLDER TREE
============================================================ */

function buildTree(){

    UI.folderTree.innerHTML="";

    Object.entries(App.categories).forEach(

        ([category,files])=>{

            const template=document

                .getElementById(

                    "treeNodeTemplate"

                )

                .content

                .cloneNode(true);

            const node=

                template.querySelector(

                    ".tree-node"

                );

            const row=

                node.querySelector(

                    ".tree-row"

                );

            const title=

                node.querySelector(

                    ".tree-title"

                );

            const children=

                node.querySelector(

                    ".tree-children"

                );

            title.textContent=

                category;

            row.addEventListener(

                "click",

                ()=>{

                    node.classList.toggle(

                        "open"

                    );

                }

            );

            files.forEach(file=>{

                const fileTemplate=document

                    .getElementById(

                        "treeFileTemplate"

                    )

                    .content

                    .cloneNode(true);

                const fileNode=

                    fileTemplate.querySelector(

                        ".tree-file"

                    );

                fileNode.querySelector(

                    ".tree-file-name"

                ).textContent=file.title;

                fileNode.onclick=()=>{

                    openFile(file);

                };

                children.appendChild(

                    fileTemplate

                );

            });

            UI.folderTree.appendChild(

                template

            );

        }

    );

}

/* ============================================================
   OPEN FILE
============================================================ */

async function openFile(file){

    App.currentFile=file;

    UI.viewer.classList.remove(

        "hidden"

    );

    UI.viewerTitle.textContent=

        file.title;

    UI.viewerPath.textContent=

        file.path;

    updateBreadcrumbs(file);

    addRecent(file);

    try{

        const content=

            await fetchFile(

                file.path

            );

        renderContent(

            file,

            content

        );

    }

    catch(error){

        UI.viewerContent.innerHTML=`

            <div class="alert danger">

                Unable to open

                ${Util.escape(file.path)}

            </div>

        `;

    }

}

/* ============================================================
   FETCH FILE
============================================================ */

async function fetchFile(path){

    if(

        APP_CONFIG.enableCaching

        &&

        App.cache[path]

    ){

        return App.cache[path];

    }

    const response=

        await fetch(path);

    if(

        !response.ok

    ){

        throw new Error(

            "Fetch failed"

        );

    }

    const text=

        await response.text();

    if(

        APP_CONFIG.enableCaching

    ){

        App.cache[path]=text;

    }

    return text;

}

/* ============================================================
   RENDER CONTENT
============================================================ */

function renderContent(

    file,

    content

){

    switch(file.extension){

        case "md":

            renderMarkdown(

                content

            );

            break;

        case "html":

            renderHTML(

                content

            );

            break;

        default:

            renderCode(

                content,

                file.extension

            );

            break;

    }

}

/* ============================================================
   MARKDOWN
============================================================ */

function renderMarkdown(text){

    const html=

        marked.parse(text);

    UI.viewerContent.innerHTML=

        `<div class="markdown-body">

        ${html}

        </div>`;

    addCopyButtons();

}

/* ============================================================
   HTML PREVIEW
============================================================ */

function renderHTML(text){

    const iframe=

        document.createElement(

            "iframe"

        );

    iframe.style.width="100%";

    iframe.style.height="80vh";

    iframe.style.border="none";

    iframe.srcdoc=text;

    UI.viewerContent.innerHTML="";

    UI.viewerContent.appendChild(

        iframe

    );

}

/* ============================================================
   CODE VIEWER
============================================================ */

function renderCode(

    text,

    extension

){

    UI.viewerContent.innerHTML=

    `

<div class="markdown-body">

<pre>

<code class="${extension}">

${Util.escape(text)}

</code>

</pre>

</div>

`;

    addCopyButtons();

}

/* ============================================================
   COPY BUTTONS
============================================================ */

function addCopyButtons(){

    UI.viewerContent

        .querySelectorAll("pre")

        .forEach(pre=>{

            const button=

                document.createElement(

                    "button"

                );

            button.className=

                "copy-btn";

            button.textContent=

                "Copy";

            button.onclick=()=>{

                navigator.clipboard.writeText(

                    pre.innerText

                );

                Util.toast(

                    "Copied"

                );

            };

            pre.appendChild(

                button

            );

        });

}

/* ============================================================
   BREADCRUMBS
============================================================ */

function updateBreadcrumbs(file){

    UI.breadcrumbs.innerHTML="";

    const items=[

        "Home",

        file.category,

        file.title

    ];

    items.forEach(

        (item,index)=>{

            const crumb=document

                .getElementById(

                    "breadcrumbTemplate"

                )

                .content

                .cloneNode(true);

            crumb.querySelector(

                ".breadcrumb-item"

            ).textContent=item;

            UI.breadcrumbs.appendChild(

                crumb

            );

            if(

                index!==items.length-1

            ){

                UI.breadcrumbs.append(

                    " / "

                );

            }

        }

    );

}
/* ============================================================
   FAVORITES
============================================================ */

function toggleFavorite(file){

    const index=App.favorites.indexOf(file.path);

    if(index===-1){

        App.favorites.unshift(file.path);

        Util.toast("Added to favorites");

    }else{

        App.favorites.splice(index,1);

        Util.toast("Removed from favorites");

    }

    Storage.save();

    renderFavorites();

    renderFiles();

}

/* ============================================================
   RECENT FILES
============================================================ */

function addRecent(file){

    App.recent=App.recent.filter(

        p=>p!==file.path

    );

    App.recent.unshift(file.path);

    if(App.recent.length>20){

        App.recent.length=20;

    }

    Storage.save();

    renderRecent();

}

/* ============================================================
   GLOBAL SEARCH
============================================================ */

const performSearch=Util.debounce(()=>{

    App.searchQuery=

        UI.globalSearch.value.trim();

    renderFiles();

},250);

function searchOverlay(query){

    UI.overlayResults.innerHTML="";

    if(!query.trim()){

        return;

    }

    const results=App.files.filter(file=>{

        const q=query.toLowerCase();

        return(

            file.title.toLowerCase().includes(q)||

            file.path.toLowerCase().includes(q)||

            file.description.toLowerCase().includes(q)||

            file.category.toLowerCase().includes(q)

        );

    });

    results.forEach(file=>{

        const div=document.createElement("div");

        div.className="search-result";

        div.innerHTML=`

            <h4>${file.title}</h4>

            <small>${file.path}</small>

        `;

        div.onclick=()=>{

            closeSearch();

            openFile(file);

        };

        UI.overlayResults.appendChild(div);

    });

}

/* ============================================================
   SEARCH OVERLAY
============================================================ */

function openSearch(){

    document

        .getElementById(

            "searchOverlay"

        )

        .classList.remove("hidden");

    UI.overlaySearch.focus();

}

function closeSearch(){

    document

        .getElementById(

            "searchOverlay"

        )

        .classList.add("hidden");

}

/* ============================================================
   THEME
============================================================ */

function toggleTheme(){

    const html=document.documentElement;

    const current=

        html.dataset.theme==="dark"

        ? "light"

        : "dark";

    html.dataset.theme=current;

    App.settings.theme=current;

    Storage.save();

}

/* ============================================================
   SIDEBAR
============================================================ */

function toggleSidebar(){

    UI.sidebar.classList.toggle(

        "open"

    );

}

/* ============================================================
   VIEWER
============================================================ */

function closeViewer(){

    UI.viewer.classList.add(

        "hidden"

    );

}

/* ============================================================
   REGISTER EVENTS
============================================================ */

function registerEvents(){

    UI.globalSearch.addEventListener(

        "input",

        performSearch

    );

    UI.sidebarSearch.addEventListener(

        "input",

        e=>{

            App.searchQuery=e.target.value;

            renderFiles();

        }

    );

    UI.overlaySearch.addEventListener(

        "input",

        e=>{

            searchOverlay(

                e.target.value

            );

        }

    );

    document

        .getElementById(

            "closeViewer"

        )

        .onclick=closeViewer;

    document

        .getElementById(

            "themeToggle"

        )

        .onclick=toggleTheme;

    document

        .getElementById(

            "sidebarToggle"

        )

        .onclick=toggleSidebar;

    document

        .getElementById(

            "searchButton"

        )

        .onclick=openSearch;

    document

        .getElementById(

            "closeSearch"

        )

        .onclick=closeSearch;

    document

        .getElementById(

            "refreshButton"

        )

        .onclick=()=>{

            renderFiles();

            renderCategories();

            renderFavorites();

            renderRecent();

            Util.toast("Refreshed");

        };

    window.addEventListener(

        "keydown",

        keyboardShortcuts

    );

}

/* ============================================================
   KEYBOARD SHORTCUTS
============================================================ */

function keyboardShortcuts(e){

    if(

        e.ctrlKey &&

        e.key==="k"

    ){

        e.preventDefault();

        openSearch();

    }

    if(

        e.key==="Escape"

    ){

        closeViewer();

        closeSearch();

    }

    if(

        e.ctrlKey &&

        e.key==="b"

    ){

        e.preventDefault();

        toggleSidebar();

    }

    if(

        e.ctrlKey &&

        e.key==="r"

    ){

        e.preventDefault();

        renderFiles();

    }

}

/* ============================================================
   CONTEXT MENU
============================================================ */

document.addEventListener(

    "contextmenu",

    e=>{

        const menu=document.getElementById(

            "contextMenu"

        );

        if(!menu){

            return;

        }

        e.preventDefault();

        menu.style.left=e.pageX+"px";

        menu.style.top=e.pageY+"px";

        menu.classList.remove("hidden");

    }

);

document.addEventListener(

    "click",

    ()=>{

        const menu=document.getElementById(

            "contextMenu"

        );

        if(menu){

            menu.classList.add("hidden");

        }

    }

);
/* ============================================================
   PERFORMANCE + HELPERS
============================================================ */

/* Lazy render (for large datasets) */
function lazyRender(list, renderFn, container){

    container.innerHTML="";

    let index=0;

    function step(){

        const chunk=list.slice(index,index+25);

        chunk.forEach(renderFn);

        index+=25;

        if(index<list.length){

            requestAnimationFrame(step);

        }

    }

    step();

}

/* ============================================================
   MANIFEST REFRESH
============================================================ */

async function refreshManifest(){

    Util.toast("Refreshing...");

    await loadManifest();

    buildStatistics();

    buildTree();

    renderFiles();

    renderCategories();

    renderFavorites();

    renderRecent();

    Util.toast("Updated");

}

/* ============================================================
   SCROLL RESTORE
============================================================ */

function saveScroll(){

    sessionStorage.setItem(

        "scroll",

        window.scrollY

    );

}

function restoreScroll(){

    const pos=

        sessionStorage.getItem("scroll");

    if(pos){

        window.scrollTo(0,parseInt(pos));

    }

}

/* ============================================================
   DRAG & DROP (future extension support)
============================================================ */

document.addEventListener(

    "dragover",

    e=>e.preventDefault()

);

document.addEventListener(

    "drop",

    e=>{

        e.preventDefault();

        Util.toast("Drop not supported yet");

    }

);

/* ============================================================
   ERROR HANDLING
============================================================ */

window.addEventListener(

    "error",

    e=>{

        console.error(e);

        Util.toast("Unexpected error occurred");

    }

);

/* ============================================================
   NETWORK HANDLING
============================================================ */

window.addEventListener(

    "offline",

    ()=>Util.toast("You are offline")

);

window.addEventListener(

    "online",

    ()=>Util.toast("Back online")

);

/* ============================================================
   BOOTSTRAP FINAL
============================================================ */

(function bootstrap(){

    // restore theme

    if(App.settings.theme){

        document.documentElement.dataset.theme=

            App.settings.theme;

    }

    // restore scroll

    restoreScroll();

    // autosave scroll

    window.addEventListener(

        "scroll",

        Util.debounce(saveScroll,200)

    );

})();