(function ($) {
    'use strict';

    var browserWindow = $(window);

    // :: 1.0 Preloader Active Code
    browserWindow.on('load', function () {
        $('.preloader').fadeOut('slow', function () {
            $(this).remove();
        });
    });

    // :: 2.0 Nav Active Code
    if ($.fn.classyNav) {
        $('#creditNav').classyNav();
    }

    // :: 3.0 Sliders Active Code
    if ($.fn.owlCarousel) {
        var welcomeSlide = $('.hero-slideshow');

        welcomeSlide.owlCarousel({
            items: 1,
            loop: true,
            nav: true,
            navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>'],
            dots: true,
            autoplay: true,
            autoplayTimeout: 10000,
            smartSpeed: 500
        });

        welcomeSlide.on('translate.owl.carousel', function () {
            var slideLayer = $("[data-animation]");
            slideLayer.each(function () {
                var anim_name = $(this).data('animation');
                $(this).removeClass('animated ' + anim_name).css('opacity', '0');
            });
        });

        welcomeSlide.on('translated.owl.carousel', function () {
            var slideLayer = welcomeSlide.find('.owl-item.active').find("[data-animation]");
            slideLayer.each(function () {
                var anim_name = $(this).data('animation');
                $(this).addClass('animated ' + anim_name).css('opacity', '1');
            });
        });

        $("[data-delay]").each(function () {
            var anim_del = $(this).data('delay');
            $(this).css('animation-delay', anim_del);
        });

        $("[data-duration]").each(function () {
            var anim_dur = $(this).data('duration');
            $(this).css('animation-duration', anim_dur);
        });
    }

    // :: 4.0 ScrollUp Active Code - DISABLED
    // The ScrollUp plugin's jQuery.easing registration was intermittently
    // getting reset before its own scroll-triggered animation ran
    // (likely due to Odoo's own async/lazy frontend asset loading on
    // this page), throwing "jQuery.easing[...] is not a function".
    // It's a cosmetic "back to top" button, not core functionality, so
    // it's disabled rather than fought with. Re-enable if/when a
    // dependency-free scroll-to-top replacement is written.
    // if ($.fn.scrollUp) {
    //     browserWindow.scrollUp({
    //         scrollSpeed: 1500,
    //         scrollText: '<i class="fa fa-angle-up"></i> Top'
    //     });
    // }

    // :: 5.0 CounterUp Active Code - DISABLED
    // The counter animation is handled by vaultedge.js using a plain
    // IntersectionObserver instead (no jQuery Waypoints dependency).
    // Keeping both active caused a feedback loop (Waypoints' own
    // doScroll/refresh cycle recursing into itself: "too much recursion")
    // when both scripts animated the same .counter elements at once.
    // if ($.fn.counterUp && $.fn.waypoint) {
    //     $('.ve-counter-item').waypoint(function() {
    //         $(this).find('.counter').counterUp({
    //             delay: 5,
    //             time: 1500
    //         });
    //     }, { offset: '95%', triggerOnce: true });
    // }

    // :: 6.0 Progress Bar Active Code
    if ($.fn.circleProgress) {
        $('#circle').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#fff',
            thickness: '3',
            reverse: true
        });
        $('#circle2').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#fff',
            thickness: '3',
            reverse: true
        });
        $('#circle3').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#fff',
            thickness: '3',
            reverse: true
        });
        $('#circle4').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
        $('#circle5').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
        $('#circle6').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
        $('#circle7').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
        $('#circle8').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
        $('#circle9').circleProgress({
            size: 90,
            emptyFill: "rgba(0, 0, 0, .0)",
            fill: '#ffbb38',
            thickness: '3',
            reverse: true
        });
    }

    // :: 7.0 Tooltip Active Code
    if ($.fn.tooltip) {
        $('[data-toggle="tooltip"]').tooltip();
    }

    // :: 8.0 Prevent Default a Click
    $('a[href="#"]').on('click', function ($) {
        $.preventDefault();
    });

    // :: 9.0 Jarallax Active Code
    if ($.fn.jarallax) {
        $('.jarallax').jarallax({
            speed: 0.2
        });
    }

    // :: 10.0 Sticky Active Code
    if ($.fn.sticky) {
        $("#sticker").sticky({
            topSpacing: 0
        });
    }

    // :: 11.0 Wow Active Code
    if (browserWindow.width() > 767) {
        new WOW().init();
    }

})(jQuery);