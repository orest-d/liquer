window.vue = new Vue({
    el: '#app',
    vuetify: new Vuetify({
        icons: {
            iconfont: 'mdi', // 'mdi' || 'mdiSvg' || 'md' || 'fa' || 'fa4' || 'faSvg'
        },
    }),
    data: {
        route: "",
        search: "",
        status: "OK",
        state: null,
        data: null,
        query: '',
        query_basis: '',
        message: "",
        html: "",
        url_submit_prefix: "/liquer/submit/",
        url_remove_prefix: "/liquer/cache/remove/",
        url_prefix: "/liquer/q/",
        url_meta_prefix: "/liquer/cache/meta/",
        metadata: null,
        metadata_log: [{ kind: "info", message: "Initial log" }],
        external_link: "",
        xlsx_link: "",
        csv_link: "",
        mode: "",
        queries_status:[],
        commands: [],
        menu: [
            {
                title: "Help", items: [
                    { title: "Homepage", link: "https://orest-d.github.io/liquer/" },
                    { title: "Commands", link: "ns-meta/flat_commands_nodoc/to_df" },
                ]
            }
        ],
        context_menu: []
    },
    vuetify: new Vuetify(),
    methods: {
        update_route: function () {
            console.log("Update", window.location.hash);
            this.route = window.location.hash.slice("1");
            if (this.route.length > 0) {
                this.submit_query(this.route);
            }
            else {
                this.load("state/state.json");
            }
        },
        info: function (txt) {
            console.log("INFO:" + txt);
            this.message = txt;
            this.status = "OK";
        },
        error: function (txt, reason) {
            console.log("ERROR:" + txt, reason);
            this.message = txt;
            this.status = "ERROR";
            if (reason.hasOwnProperty("body")) {
                this.html = reason.body;
            }
        },
        goto_rel: function (link) {
            console.log("GOTO REL", link);
            if (link.indexOf(":") == -1) {
                if (link.startsWith('/')) {
                    link = link.slice(1);
                }
                else {
                    link = this.query_basis + '/' + link;
                }
                window.location.href = "#" + link;
                this.submit_query(link);
            }
            else {
                this.update_link = true;
                window.location.href = "#";
                this.external_link = link;
                this.mode = "iframe";
            }
        },
        goto: function (link) {
            console.log("GOTO", link);
            if (link.indexOf(":") == -1) {
                window.location.href = "#" + link;
                this.submit_query(link);
            }
            else {
                this.update_link = true;
                window.location.href = "#";
                this.external_link = link;
                this.mode = "iframe";
            }
        },
        clean_cache: function () {
            console.log("Clean cache called");
            this.$http.get(this.url_prefix + "/clean_cache").then(function (response) {
                console.log("Clean cache result:", response.body);
                this.info("Cache cleaned");
            }.bind(this), function (reason) { this.error("Cache cleaning error", reason); }.bind(this));

        },
        load_metadata: function (query) {
            console.log("Load metadata", query);
            this.$http.get(this.url_meta_prefix + query).then(function (response) {
                response.json().then(function (data) {
                    if (data == null) {
                        this.metadata = { status: "undefined", log: [] };
                    }
                    else {
                        this.metadata = data;
                    }
                    try {
                        this.metadata_log = this.metadata.log;
                    }
                    catch (error) {
                        console.log(error);
                        this.metadata_log = [{ kind: "info", message: "No valid metadata yet (load_metadata)" }];
                    }
                });
            });
        },
        refresh_metadata: function () {
            console.log("Refresh metadata", this.query);
            this.$http.get(this.url_meta_prefix + this.query).then(function (response) {
                response.json().then(function (data) {
                    console.log(data);
                    if (data == null) {
                        this.metadata = { status: "undefined", log: [] };
                    }
                    else {
                        this.metadata = data;
                    }
                    try {
                        this.metadata_log = this.metadata.log;
                    }
                    catch (error) {
                        console.log(error);
                        this.metadata_log = [{ kind: "info", message: "No valid metadata yet (refresh_metadata)" }];
                    }
                    if (data == null || (this.metadata.status != "ready" && this.metadata.status != "error")) {
                        console.log("refresh",this.metadata.status);
                        window.setTimeout(this.refresh_metadata, 500);
                    }
                    else {
                        if (this.metadata.status == "ready") {
                            this.load(this.query);
                        }
                    }
                }.bind(this), function (reason) { this.error("Json error (refresh metadata)", reason); }.bind(this));
            }.bind(this), function (reason) { this.error("API call error (refresh metadata)", reason); }.bind(this));
        },
        submit_query: function (query) {
            console.log("Submit", query);
            this.query = query;
            this.$http.get(this.url_submit_prefix + query).then(function (response) {
                response.json().then(function (data) {
                    this.metadata = data;
                    this.refresh_metadata();
                }.bind(this), function (reason) { this.error("Json error (submit query)", reason); }.bind(this));
            }.bind(this), function (reason) { this.error("API call error (submit query)", reason); }.bind(this));
        },
        remove_query: function (query) {
            console.log("Remove", query);
            this.query = query;
            this.$http.get(this.url_remove_prefix + query).then(function (response) {
                response.json().then(function (data) {
                    this.metadata = data;
                    this.refresh_metadata();
                }.bind(this), function (reason) { this.error("Json error (remove query)", reason); }.bind(this));
            }.bind(this), function (reason) { this.error("API call error (remove query)", reason); }.bind(this));
        },
        inspect_query: function (query){
            this.mode="inspect";
            this.submit_query(query);
        },
        view_query: function (query){
            this.mode="iframe";
            this.query = query;
            this.refresh_metadata();
        },
        get_queries_status: function () {
            console.log("get_queries_status");
            this.$http.get(this.url_prefix + "ns-meta/queries_status/queries_status.json").then(function (response) {
                response.json().then(function (data) {
                    this.queries_status = data;
                    if (this.mode=="queries_status"){
                        window.setTimeout(this.get_queries_status, 500);
                    }
                }.bind(this), function (reason) { this.error("Json error (get_queries_status)", reason); }.bind(this));
            }.bind(this), function (reason) { this.error("API call error (get_queries_status)", reason); }.bind(this));
        },
        query_status_mode:function(){
            this.mode="queries_status";
            this.get_queries_status();
        },
        load: function (query) {
            this.xlsx_link = "";
            this.csv_link = "";
            this.load_metadata(query);
            if (this.update_link) {
                console.log("Update link prevented loading");
                this.update_link = false;
                return;
            }
            console.log("Load", query);
            var q = query.split("/").filter(function (x) { return x.length; });

            this.query = query;
            if (q.length > 0) {
                var last = q[q.length - 1];
                var path = query;
                var query_basis = query;
                var extension = "";
                var filename = last.replace("-", "_");
                if (last.indexOf("-") == -1 && last.indexOf(".") != -1) {
                    query_basis = q.slice(0, q.length - 1).join("/");
                    var v = last.split(".");
                    filename = v[0];
                    extension = v[v.length - 1];
                }
                this.query_basis = query_basis;
                this.status = "LOADING";
                this.mode = "";
                console.log("query_basis", query_basis)
                console.log("Load state", this.url_prefix + query_basis + "/state/state.json");
                this.$http.get(this.url_prefix + query_basis + "/state/state.json").then(function (response) {
                    response.json().then(function (data) {
                        this.data = null;
                        this.state = data;
                        this.metadata = data;
                        try {
                            this.menu = this.state.vars.menu;
                        }
                        catch (error) {
                            console.log("No menu:", error);
                        }
                        try {
                            this.context_menu = this.state.attributes.context_menu;
                        }
                        catch (error) {
                            console.log("No context menu:", error);
                        }

                        this.html = "";
                        this.info("State loaded.");

                        if (this.state.type_identifier == "dataframe") {
                            if (extension == "") {
                                console.log("dataframe -> append .json");
                                path += "/data.json";
                            }
                            this.csv_link = this.url_prefix + query_basis + "/" + filename + ".csv";
                            this.xlsx_link = this.url_prefix + query_basis + "/" + filename + ".xlsx";
                        }
                        if (this.state.type_identifier == "matplotlibfigure") {
                            if (extension == "") {
                                console.log("matplotlibfigure -> append .png");
                                path += "/image.png";
                            }
                        }
                        if (this.state.extension == "json" || path.endsWith(".json")) {
                            this.status = "LOADING";
                            console.log("Load json data", this.url_prefix + path);
                            this.$http.get(this.url_prefix + path).then(function (response) {
                                response.json().then(function (data) {
                                    this.html = "";
                                    this.data = data;
                                    this.info("Data loaded.");
                                    if (this.state.type_identifier == "dataframe") {
                                        this.mode = "dataframe";
                                    }
                                }.bind(this), function (reason) { this.error("Json error (data)", reason); }.bind(this));
                            }.bind(this), function (reason) { this.error("Data loading error", reason); }.bind(this));
                        }
                        else if (this.state.extension == "html" || this.state.extension == "htm" || path.endsWith(".html") || path.endsWith(".htm")) {
                            console.log("html mode");
                            this.external_link = this.url_prefix + path;
                            this.mode = "iframe";
                        }
                        else if (this.state.extension == "png" ||
                            this.state.extension == "jpg" ||
                            this.state.extension == "jpeg" ||
                            path.endsWith(".png") ||
                            path.endsWith(".jpg") ||
                            path.endsWith(".svg") ||
                            path.endsWith(".jpeg")) {
                            console.log("image mode");
                            this.external_link = this.url_prefix + path;
                            this.mode = "image";
                        }
                        else {
                            console.log("iframe mode by default");
                            this.external_link = this.url_prefix + path;
                            this.mode = "iframe";
                        }
                    }.bind(this), function (reason) { this.error("Json error (state)", reason); }.bind(this));
                }.bind(this), function (reason) { this.error("State loading error", reason); }.bind(this));
            }
            else {
                this.data = null;
                this.status = "LOADING";
                console.log("Load state (2) ", this.url_prefix + "state/state.json");
                this.$http.get(this.url_prefix + "state/state.json").then(function (response) {
                    response.json().then(function (data) {
                        this.data = null;
                        this.state = data;
                        this.html = "";
                        this.mode = "";
                        this.info("State loaded.");
                    }.bind(this), function (reason) { this.error("Json error (state)", reason); }.bind(this));
                }.bind(this), function (reason) { this.error("State loading error", reason); }.bind(this));
            }
        },
        safearg: function (arg) {
            try {
                return { value: arg[0], label: arg[1].label, type: arg[1].type };
            }
            catch (error) {
                return { value: "?", label: "?", type: "?" };
            }
        },
        data_status_color: function (status) {
            if (status == "none") {
                return "gray";
            }
            if (status == "obsolete") {
                return "gray";
            }
            if (status == "finished") {
                return "gray";
            }
            if (status == "ready") {
                return "blue";
            }
            if (status == "evaluating parent") {
                return "yellow";
            }
            if (status == "evaluating dependencies") {
                return "orange";
            }
            if (status == "evaluation") {
                return "green";
            }
            if (status == "error") {
                return "red";
            }
            return "gray";
        }
    },
    computed: {
        waiting_mode: function(){
            return (this.presentation_mode && (this.metadata.status!='ready'));
        },
        presentation_mode: function(){
            return ((this.mode == "iframe") || (this.mode=='dataframe') || (this.mode=='image'));
        },
        status_color: function () {
            if (this.status == "OK") {
                return "green";
            }
            if (this.status == "ERROR") {
                return "red";
            }
            return "gray";
        },
        dataframe_headers: function () {
            if (this.data == null) {
                return [];
            }
            else {
                var h = [
                ];

                this.data.schema.fields.forEach(
                    function (x) {
                        h.push({
                            text: x.name, value: x.name
                        });
                    }
                );
                console.log(h);
                return h;
            }
        },
        dataframe_rows: function () {
            if (this.data == null) {
                return [];
            }
            else {
                console.log("rows", this.data.data)
                return this.data.data;
            }
        },
        commands_headers: function () {
            return [
                { text: "Namespace", value: "ns" },
                { text: "Command", value: "name" },
                { text: "Description", value: "doc" },
                { text: "Example", value: "example_link" },
            ];
        },
        commands_rows: function () {
            if (this.data == null) {
                return [];
            }
            else {
                return this.commands;
            }
        },
        metadata_log_slice: function () {
            try {
                return this.metadata_log.slice(Math.max(metadata.log.length - 5, 0));
            }
            catch (error) {
                console.log(error);
                return [{ kind: "info", message: "Empty log" }];
            }
        }

    },
    created: function () {
        this.$http.get(this.url_prefix + "ns-meta/flat_commands/commands.json").then(function (response) {
            response.json().then(function (data) {
                this.commands = data;
                this.info("Commands loaded.");
            }.bind(this), function (reason) { this.error("Json error (commands)", reason); }.bind(this));
        }.bind(this), function (reason) { this.error("Data loading error", reason); }.bind(this));

        window.onhashchange = this.update_route
        this.update_route();
    },
});