function simple_GET(path, callback){
  var xmlhttp = new XMLHttpRequest();
  xmlhttp.open('GET', path, true);
  xmlhttp.onreadystatechange = function() {
  if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
      callback(xmlhttp.responseText);
    }
  };
  xmlhttp.send(null);
}

var app = new Vue({
  delimiters: ['[[', ']]'],
  el: "#app",
  data: {
    artists:[],
	tags:[],
    results:[],
    shop:[]
  },
  computed: {
   	yesLogin: function() {
		if (this.$cookies.get('userName') != null && this.$cookies.get('userName') != '""'){
			var self = this;
			self.name = this.$cookies.get('userName');
			return true;
		}else{
			return false;
		}
	},
   	noLogin: function() {
		if (this.$cookies.get('userName') == null || this.$cookies.get('userName') == '""'){
			return true;
		}else{
			return false;
		}
	}
  },
  methods: {
	loadCate: function(resp) {
		var self = this;
		self.categories = JSON.parse(resp);
	},
	loadRanking: function(resp) {
		var self = this;
		self.ranking = JSON.parse(resp);
	},
	loadSearch: function(resp) {
		var self = this;
		self.results = JSON.parse(resp);
	},
	loadShop: function(resp) {
		var self = this;
		self.shop = JSON.parse(resp);
	},
	loadMenu: function(resp) {
		var self = this;
		self.menus = JSON.parse(resp);
	},
	loadUser: function(resp) {
		var self = this;
		self.user = JSON.parse(resp);
	}
  },
  created: function () {
    switch(location.pathname){
        case '/tag_search.html':
            simple_GET("api/tag_search"+location.search,this.loadSearch);
			break;
        case '/word_search.html':
            simple_GET("api/word_search"+location.search,this.loadSearch);
			break;
        case '/shop.html':
            simple_GET("api/shop"+location.search,this.loadShop);
            //simple_GET("api/menu"+location.search,this.loadMenu);
			break;
        case '/user.html':
            simple_GET("api/user?k="+$cookies.get('userName'),this.loadUser);
			break;
    }
  },
})