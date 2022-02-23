function DarkenPageWithLoading() {
    var loadTopPos;
    $(".DarkBg").remove();
    $("body").prepend("<div class='DarkBg justify-content-center align-items-center'><div class='h-100 d-flex justify-content-center align-items-center m-0 p-0' style='filter: grayscale(100%); -webkit-filter: grayscale(100%);'><img src='/static/images/loading.webp' width='20%' /></div></div>");

        $(".DarkBg").css({
            "height": $(document).height() + "px",
        });

        $(window).on("load resize", function () {
            $(".DarkBg").css({
                "width": document.body.scrollWidth + "px"
            });
        });


}

function LightenPage() {
    $(document).ready(function () {
        $(".DarkBg").remove();
    });
}