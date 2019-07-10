//2階層目のメニューを表示する
$('.dropdown-submenu > a').on("click", function(e) {
    var submenu = $(this);
    $('.dropdown-submenu .dropdown-menu').removeClass('show');
    submenu.next('.dropdown-menu').addClass('show');
    e.stopPropagation();
});

//他のボタンが押されたら非表示にする
$('.dropdown').on("hidden.bs.dropdown", function() {
    $('.dropdown-menu.show').removeClass('show');
});

//検索フォームクリックで検索ページへ
function input_search(key_code){
    if(key_code===13){
        window.location.href = '/word_search.html?q='+$("#search_form").val();
    }
}
//検索フォームクリックで検索ページへ
$('#w_search').on("click",function(e) {
	window.location.href = '/word_search.html?q='+$("#search_form").val();
});

var params = new URLSearchParams(location.search.slice(1));
//無理やり
if ($cookies.get('lang')==null){
    $cookies.set('lang',"ja");
}
if(params.get("lang")=="en"){
    $cookies.set('lang',"en");
}
if(params.get("lang")=="ja"){
    $cookies.set('lang',"ja");
}

//翻訳
const glot = new Glottologist();
glot.import("/api/translate.json").then(() => {
    glot.render($cookies.get('lang'));
})