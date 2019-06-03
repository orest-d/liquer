window.onload = function () {

    window.app = new Vue({
        el: "#app",
        data: {
            view: 'home',
            commands: {},
            status: "OK",
            status_color: "green",
            message: "",
            message_on: false,
            query: "",
            query_response: "",
            query_debug: {},
            ql:[],
            qfilename:""            
        },
        methods: {
            error: function (message, reason) {
                this.status = "ERROR";
                this.status_color = "red";
                this.message = message;
                console.log("ERROR:" + message, reason);
            },
            info: function (message) {
                this.status = "OK";
                this.status_color = "";
                this.message = message;
                console.log("INFO:" + message);
            },
            build_query:function(){
                this.ql=[["abc","def"],["xyz","123"]];
                this.info("Build query: ", this.ql);
                this.$http.post("../api/build", {ql:this.ql}).then(
                    function (response) {
                        response.json().then(function (data) {
                            this.query = data.query;
                            this.message = data.message;
                            this.status = data.status;
                            this.info("Build query executed.");
                        }.bind(this), function (reason) { this.error("Build query parsing error:", reason); }.bind(this));
                    }.bind(this), function (reason) { this.error("Build query error:", reason); }.bind(this)); 
            },
            execute_query: function () {
                this.info("Execute query: " + this.query);
                this.query_response = "";
                this.query_debug={};
                this.$http.get("../q/" + this.query).then(
                    function (response) {
                        response.text().then(function (data) {
                            this.query_response = data;
                            this.info("Query executed.");
                        }.bind(this), function (reason) { this.error("Query result parsing error:", reason); }.bind(this));
                    }.bind(this), function (reason) { this.error("Query execution error:", reason); }.bind(this));

                this.$http.get("../api/debug-json/" + this.query).then(
                    function (response) {
                        response.json().then(function (data) {
                            this.query_debug = data;
                            this.info("Query debug executed.");
                        }.bind(this), function (reason) { this.error("Query debug parsing error:", reason); }.bind(this));
                    }.bind(this), function (reason) { this.error("Query debug error:", reason); }.bind(this));
            }
        },
        created: function () {
            this.$http.get("../api/commands.json").then(function (response) {
                response.json().then(function (data) {
                    this.commands = data;
                    this.info("Commands loaded.");
                }.bind(this), function (reason) { this.error("Json error:", reason); }.bind(this));
            }.bind(this), function (reason) { this.error("Commands loading error:", reason); }.bind(this));
        }

    });
};
