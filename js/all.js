(function($){
    "use strict"; // Start of use strict
    
    
    /* ---------------------------------------------
     Scripts initialization
     --------------------------------------------- */
    
    $(window).on("load", function(){
        
        // Page loader        
        $(".page-loader div").fadeOut();
        $(".page-loader").delay(200).fadeOut("slow");
        
        init_text_rotator();
        initWorkFilter();
        init_scroll_navigate();
        init_wow();
        init_parallax();
        initPageSliders();
        
        $(window).trigger("scroll");
        $(window).trigger("resize");        
        
        // Hash menu forwarding
        if ((window.location.hash) && ($(window.location.hash).length)) {
            var hash_offset = $(window.location.hash).offset().top;
            $("html, body").animate({
                scrollTop: hash_offset
            });
        }
  
    });    
    
    $(document).ready(function(){
        $(window).trigger("resize");            
        init_classic_menu();
        init_lightbox();        
        init_team();
        init_services();        
        init_map();
        init_bg_video();
        Splitting();
        init_shortcodes();
        init_tooltips();
        init_masonry();
    });    
    
    $(window).resize(function(){
        init_classic_menu_resize();        
        // 100vh height on mobile devices
        var vh = $(window).height() * 0.01;
        $("html").css("--vh", vh + "px");
    });
    
    
    /* --------------------------------------------
     Platform detect
     --------------------------------------------- */
    
    var mobileTest;
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)) {
        mobileTest = true;
        $("html").addClass("mobile");
    }
    else {
        mobileTest = false;
        $("html").addClass("no-mobile");
    }    
    var mozillaTest;
    if (/mozilla/.test(navigator.userAgent)) {
        mozillaTest = true;
    }
    else {
        mozillaTest = false;
    }
    var safariTest;
    if (/safari/.test(navigator.userAgent)) {
        safariTest = true;
    }
    else {
        safariTest = false;
    }
    
    // Detect touch devices    
    if (!("ontouchstart" in document.documentElement)) {
        document.documentElement.className += " no-touch";
    } else {
        document.documentElement.className += " touch";
    }
    
    
    /* ---------------------------------------------
     Sections helpers
     --------------------------------------------- */
    
    // Sections backgrounds    
    var pageSection = $(".home-section, .page-section, .small-section, .split-section");
    pageSection.each(function(indx){        
        if ($(this).attr("data-background")){
            $(this).css("background-image", "url(" + $(this).data("background") + ")");
        }
    });
    
    // Function for block height 100%
    function height_line(height_object, height_donor){
        height_object.height(height_donor.height());
        height_object.css({
            "line-height": height_donor.height() + "px"
        });
    }
    function height_line_s(height_object, height_donor){
        height_object.height(height_donor.height());
        height_object.css({
            "line-height": height_donor.height() - 2 + "px"
        });
    }   
    
    // Progress bars
    var progressBar = $(".progress-bar");
    progressBar.each(function(indx){
        $(this).css("width", $(this).attr("aria-valuenow") + "%");
    });
    
    
    /* ---------------------------------------------
     Nav panel classic
     --------------------------------------------- */
    
    var mobile_nav = $(".mobile-nav");
    var desktop_nav = $(".desktop-nav");
    
    mobile_nav.attr("aria-expanded", "false");
    
    function init_classic_menu_resize(){
        
        // Mobile menu max height
        $(".mobile-on .desktop-nav > ul").css("max-height", $(window).height() - $(".main-nav").height() - 20 + "px");
        
        // Mobile menu style toggle
        if ($(window).width() <= 1024) {
            $(".main-nav").addClass("mobile-on");
            $(".mobile-cart").show();
        }
        else 
            if ($(window).width() > 1024) {
                $(".main-nav").removeClass("mobile-on");
                desktop_nav.show();
                $(".mobile-cart").hide();
            }
    }
    
    function init_classic_menu(){    
        
        if ($(".main-nav").hasClass("transparent")){
            height_line($(".inner-nav > ul > li > a"), $(".main-nav"));
        } else {
        	height_line_s($(".inner-nav > ul > li > a"), $(".main-nav"));
        }
        height_line(mobile_nav, $(".main-nav"));
        height_line($(".mobile-cart"), $(".main-nav"));
        
        // Transpaner menu
                
        if ($(".main-nav").hasClass("transparent")){
           $(".main-nav").addClass("js-transparent"); 
        } else if (!($(".main-nav").hasClass("dark"))){
           $(".main-nav").addClass("js-no-transparent-white");
        }
        
        $(window).scroll(function(){        
            
            if ($(window).scrollTop() > 0) {
                $(".js-transparent").removeClass("transparent");
                $(".main-nav, .nav-logo-wrap .logo, .mobile-nav, .mobile-cart").addClass("small-height");
                $(".light-after-scroll").removeClass("dark");
                $(".main-nav").addClass("body-scrolled");
            }
            else if ($(window).scrollTop() === 0){
                $(".js-transparent").addClass("transparent");
                $(".main-nav, .nav-logo-wrap .logo, .mobile-nav, .mobile-cart").removeClass("small-height");
                $(".light-after-scroll").addClass("dark");
                $(".main-nav").removeClass("body-scrolled");
            }
            
            
        });
        
        // Mobile menu toggle
        
        mobile_nav.click(function(){
                  
            if (desktop_nav.hasClass("js-opened")) {
                desktop_nav.slideUp("slow", "easeOutExpo").removeClass("js-opened");
                $(this).removeClass("active");
                $(this).attr("aria-expanded", "false");
            }
            else {
                desktop_nav.slideDown("slow", "easeOutQuart").addClass("js-opened");
                $(this).addClass("active");
                $(this).attr("aria-expanded", "true");
                // Fix for responsive menu
                if ($(".main-nav").hasClass("not-top")){
                    $(window).scrollTo(".main-nav", "slow"); 
                }                
            }   
                     
        });
        
        $(document).on("click", function(event){            
            if ($(window).width() <= 1024) {
                var $trigger = $(".main-nav");
                if ($trigger !== event.target && !$trigger.has(event.target).length) {
                    desktop_nav.slideUp("slow", "easeOutExpo").removeClass("js-opened");
                    mobile_nav.removeClass("active");
                    mobile_nav.attr("aria-expanded", "false");
                }
            }
        });
        
        mobile_nav.keydown(function(e){
            if (e.keyCode == 13 || e.keyCode == 32) {
                if (desktop_nav.hasClass("js-opened")) {
                    desktop_nav.slideUp("slow", "easeOutExpo").removeClass("js-opened");
                    $(this).removeClass("active");
                    $(this).attr("aria-expanded", "false");
                }
                else {
                    desktop_nav.slideDown("slow", "easeOutQuart").addClass("js-opened");
                    $(this).addClass("active");
                    $(this).attr("aria-expanded", "true");
                    // Fix for responsive menu
                    if ($(".main-nav").hasClass("not-top")) {
                        $(window).scrollTo(".main-nav", "slow");
                    }
                }
            }        
        });
        
        desktop_nav.find("a:not(.mn-has-sub)").click(function(){
            if (mobile_nav.hasClass("active")) {
                desktop_nav.slideUp("slow", "easeOutExpo").removeClass("js-opened");
                mobile_nav.removeClass("active");
                mobile_nav.attr("aria-expanded", "false");
            }
        });
        
        
        // Sub menu
        
        var mnHasSub = $(".mn-has-sub");
        var mnThisLi;
        
        mnHasSub.attr({
            "role": "button",
            "aria-expanded": "false",
            "aria-haspopup": "true"
        });
        
        mnHasSub.click(function(){
        
            if ($(".main-nav").hasClass("mobile-on")) {
                mnThisLi = $(this).parent("li:first");
                if (mnThisLi.hasClass("js-opened")) {
                    $(this).attr("aria-expanded", "false");
                    mnThisLi.find(".mn-sub:first").slideUp(function(){
                        mnThisLi.removeClass("js-opened");
                    });
                }
                else {
                    $(this).attr("aria-expanded", "true");
                    mnThisLi.addClass("js-opened");
                    mnThisLi.find(".mn-sub:first").slideDown();
                }
                
                return false;
            }
            
        });
        
        mnThisLi = mnHasSub.parent("li");
        mnThisLi.hover(function(){
        
            if (!($(".main-nav").hasClass("mobile-on"))) {
                $(this).find(".mn-has-sub:first")
                    .attr("aria-expanded", "true")
                    .addClass("js-opened");
                $(this).find(".mn-sub:first").stop(true, true).fadeIn("fast");
            }
            
        }, function(){
        
            if (!($(".main-nav").hasClass("mobile-on"))) {
                $(this).find(".mn-has-sub:first")
                    .attr("aria-expanded", "false")
                    .removeClass("js-opened");
                $(this).find(".mn-sub:first").stop(true, true).delay(100).fadeOut("fast");
            }
            
        });
        
        /* Keyboard navigation for main menu */
       
        mnHasSub.keydown(function(e){            
        
            if ($(".main-nav").hasClass("mobile-on")) {                
                if (e.keyCode == 13 || e.keyCode == 32) {                
                    mnThisLi = $(this).parent("li:first");
                    if (mnThisLi.hasClass("js-opened")) {
                        $(this).attr("aria-expanded", "false");
                        mnThisLi.find(".mn-sub:first").slideUp(function(){                            
                            mnThisLi.removeClass("js-opened");
                        });
                    }
                    else {
                        $(this).attr("aria-expanded", "true");
                        mnThisLi.addClass("js-opened");
                        mnThisLi.find(".mn-sub:first").slideDown();
                    }
                    
                    return false;
                }
            }
            
        });
        
        $(".inner-nav a").focus(function(){
            if (!($(".main-nav").hasClass("mobile-on")) && ($("html").hasClass("no-touch")) && (!($(this).parent("li").find(".mn-sub:first").is(":visible")))) {
                $(this).parent("li").parent().children().find(".mn-has-sub:first")
                    .attr("aria-expanded", "false")
                    .removeClass("js-opened");
                $(this).parent("li").parent().children().find(".mn-sub:first").stop(true, true).delay(100).fadeOut("fast");
            }
        });
     
        $(".inner-nav a").first().keydown(function(e){
            if (!($(".main-nav").hasClass("mobile-on"))) {
                if (e.shiftKey && e.keyCode == 9) {
                    $(this).parent("li").find(".mn-has-sub:first")
                        .attr("aria-expanded", "false")
                        .removeClass("js-opened");
                    $(this).parent("li").find(".mn-sub:first").stop(true, true).delay(100).fadeOut("fast");
                }
            }
        });
        
        $(".mn-sub li:last a").keydown(function(e){
            if (!($(".main-nav").hasClass("mobile-on"))) {
                if (!e.shiftKey && e.keyCode == 9) {
                    $(this).parent("li").parent().parent().find(".mn-has-sub:first")
                        .attr("aria-expanded", "false")
                        .removeClass("js-opened");
                    $(this).parent("li").parent().stop(true, true).delay(100).fadeOut("fast");
                }
            }
        }); 

        $(document).keydown(function(e){
            if (!($(".main-nav").hasClass("mobile-on"))) {
                if (e.keyCode == 27) {
                    if (mnHasSub.parent("li").find(".mn-sub:first li .mn-sub").is(":visible")){
                        mnHasSub.parent("li").find(".mn-sub:first li .mn-has-sub")
                            .attr("aria-expanded", "false")
                            .removeClass("js-opened");
                        mnHasSub.parent("li").find(".mn-sub:first li .mn-sub").stop(true, true).delay(100).fadeOut("fast");
                    } else{
                        mnHasSub.parent("li").find(".mn-has-sub:first")
                            .attr("aria-expanded", "false")
                            .removeClass("js-opened");
                        mnHasSub.parent("li").find(".mn-sub:first").stop(true, true).delay(100).fadeOut("fast");
                    }
                    
                }
            }
        });
         
        mnHasSub.on("click", function () { 
            if (!($(".main-nav").hasClass("mobile-on"))) {                
                if (!($(this).hasClass("js-opened"))){
                    $(this).addClass("js-opened");
                    $(this).attr("aria-expanded", "true");
                    $(this).parent("li").find(".mn-sub:first").fadeIn("fast");
                    return false;
                }
                else{
                    $(this).removeClass("js-opened");
                    $(this).attr("aria-expanded", "false");
                    $(this).parent("li").find(".mn-sub:first").fadeOut("fast");
                    return false;
                }                
            }            
        });
        
    }
    
    
    /* ---------------------------------------------
     Scroll navigation
     --------------------------------------------- */
    
    function init_scroll_navigate(){
        
        $(".local-scroll").localScroll({
            target: "body",
            duration: 1500,
            offset: 0,
            easing: "easeInOutQuart",
            onAfter: function(anchor, settings){
                anchor.focus();
                if (anchor.is(":focus")) {
                    return !1;
                }
                else {
                    anchor.attr("tabindex", "-1");
                    anchor.focus()
                }        
            }
        });
        
        var sections = $(".home-section, .split-section, .page-section");
        var menu_links = $(".scroll-nav li a");
        
        $(window).scroll(function(){
        
            sections.filter(":in-viewport:first").each(function(){
                var active_section = $(this);
                var active_link = $('.scroll-nav li a[href="#' + active_section.attr("id") + '"]');
                menu_links.removeClass("active");
                active_link.addClass("active");
            });
            
        });
        
    }
    
    
    /* ---------------------------------------------
     Lightboxes
     --------------------------------------------- */
    
    function init_lightbox(){
    
        // Works Item Lightbox				
        $(".work-lightbox-link").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        	
        // Other Custom Lightbox
        $(".lightbox-gallery-1").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-2").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-3").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-4").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-5").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-6").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-7").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-8").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-9").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox-gallery-10").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        $(".lightbox").magnificPopup({
            gallery: {
                enabled: true
            },
            mainClass: "mfp-fade"
        });
        
    }
    
    
    /* -------------------------------------------
     Parallax
     --------------------------------------------- */
    
    function init_parallax(){
        if (($(window).width() >= 1024) && (mobileTest == false) && $("html").hasClass("no-touch")) {
            $(".parallax-1").each(function(){$(this).parallax("50%", 0.1);});
            $(".parallax-2").each(function(){$(this).parallax("50%", 0.2);});
            $(".parallax-3").each(function(){$(this).parallax("50%", 0.3);});
            $(".parallax-4").each(function(){$(this).parallax("50%", 0.4);});
            $(".parallax-5").each(function(){$(this).parallax("50%", 0.5);});
            $(".parallax-6").each(function(){$(this).parallax("50%", 0.6);});
            $(".parallax-7").each(function(){$(this).parallax("50%", 0.7);});
            $(".parallax-8").each(function(){$(this).parallax("50%", 0.8);});
            $(".parallax-9").each(function(){$(this).parallax("50%", 0.9);});
            $(".parallax-10").each(function(){$(this).parallax("50%", 0.1);});
        }
    }
    
    
    /* -------------------------------------------
     Text Rotator
     --------------------------------------------- */
    
    function init_text_rotator(){
        $(".text-rotate").each(function(){            
            var text_rotator = $(this);
            var text_rotator_cont = text_rotator.html();
            text_rotator.attr("aria-hidden", "true");
            text_rotator.before("<span class='sr-only'>" + text_rotator_cont + "</span>");
            text_rotator.Morphext({
                animation: "fadeIn",
                separator: ",",
                speed: 4000
            });            
        });
    }
    
    
    /* ---------------------------------------------
     Shortcodes
     --------------------------------------------- */
    
    function init_shortcodes(){
        
        // Accordion        
        $(".accordion").each(function(){
            var allPanels = $(this).children("dd").hide();
            var allTabs = $(this).children("dt").children("a");
            allTabs.attr("role", "button");
            $(this).children("dd").first().slideDown("easeOutExpo");
            $(this).children("dt").children("a").first().addClass("active");
            $(this).children("dt").children("a").attr("aria-expanded", "false");
            $(this).children("dt").children("a").first().attr("aria-expanded", "true");
                        
            $(this).children("dt").children("a").click(function(){        
                var current = $(this).parent().next("dd");
                allTabs.removeClass("active");
                $(this).addClass("active");
                allTabs.attr("aria-expanded", "false");
                $(this).attr("aria-expanded", "true");
                allPanels.not(current).slideUp("easeInExpo");
                $(this).parent().next().slideDown("easeOutExpo");                
                return false;                
            });
            
         });        
        
        // Toggle
        var allToggles = $(".toggle > dd").hide();
        var allTabs = $(".toggle > dt > a");
        allTabs.attr({
            "role": "button",
            "aria-expanded": "false"
            });
        
        $(".toggle > dt > a").click(function(){
        
            if ($(this).hasClass("active")) {            
                $(this).parent().next().slideUp("easeOutExpo");
                $(this).removeClass("active");
                $(this).attr("aria-expanded", "false");                
            }
            else {
                var current = $(this).parent().next("dd");
                $(this).addClass("active");
                $(this).attr("aria-expanded", "true");
                $(this).parent().next().slideDown("easeOutExpo");
            }
            
            return false;
        });
        
        // Responsive video
        $(".video, .resp-media, .blog-media").fitVids();
        $(".work-full-media").fitVids(); 
               
    }
    
    
    /* ---------------------------------------------
     Tooltips (bootstrap plugin activated)
     --------------------------------------------- */
    
    function init_tooltips(){
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl){
            return new bootstrap.Tooltip(tooltipTriggerEl)
        })
    }
    
    
    /* ---------------------------------------------
     Team
     --------------------------------------------- */   
     
    function init_team(){
    
        // Hover        
        $(".team-item").click(function(){
            if ($("html").hasClass("mobile")) {
                $(this).toggleClass("js-active");
            }
        });
        
        // Keayboar navigation for team section        
        $(".team-social-links > a").on("focus blur", function(){
             if (!($("html").hasClass("mobile"))) {
                 $(this).parent().parent().parent().parent().toggleClass("js-active");
             }       
        });
        
    }
    
    
    /* ---------------------------------------------
     Services
     --------------------------------------------- */   
     
    function init_services(){        
        var services_more;
        var services_title;
        $(".services-item").each(function(){
            services_title = $(this).find(".services-title").html();
            services_more = $(this).find(".services-more > .text-link").html();
            $(this).find(".services-more > .text-link").html(services_more + '<span class="sr-only"> about ' + services_title + '</span>');
        });
    }
    
    
})(jQuery); // End of use strict


/* ---------------------------------------------
 Sliders
 --------------------------------------------- */

function initPageSliders(){
    (function($){
        "use strict";
        
        function owl_keynav(el){
            el.attr({
                "role": "region",
                "aria-roledescription": "carousel"
            });         
            el.find(".owl-prev, .owl-next").attr({
                "role": "button",
                "tabindex": "0"
            });
            el.prepend(el.find(".owl-controls"));     
            el.on("click", ".owl-page, .owl-prev, .owl-next", function(e){
                var this_owl = el.data("owlCarousel");
                this_owl.stop();
            });            
            el.on("keydown", ".owl-prev", function(e){
                if (e.keyCode == 13 || e.keyCode == 32) {
                    var this_owl = el.data("owlCarousel");
                    this_owl.prev();
                    return false;                    
                }
            });
            el.on("keydown", ".owl-next", function(e){
                if (e.keyCode == 13 || e.keyCode == 32) {
                    var this_owl = el.data("owlCarousel");
                    this_owl.next();
                    return false;                   
                }
            });
        }
        
        function owl_update(el){       
            el.find(".owl-item").attr({
                "aria-hidden": "true"
            });
            el.find(".owl-item.active").removeAttr("aria-hidden");
            el.find(".owl-item a, .owl-item button, .owl-item input").attr({
                "tabindex": "-1"
            });
            el.find(".owl-item.active a, .owl-item.active button, .owl-item.active input").attr({
                "tabindex": "0"
            });
        }
        
        // Fullwidth slider
        $(".fullwidth-slider").owlCarousel({
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Fullwidth slider fade
        $(".fullwidth-slider-fade").owlCarousel({
            transitionStyle: "fade",
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Fullwidth slider fadezoom
        $(".fullwidth-slider-fadezoom").owlCarousel({
            transitionStyle: "fadeUp",
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Text slider
        $(".text-slider").owlCarousel({
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Fullwidth gallery
        $(".fullwidth-gallery").owlCarousel({
            transitionStyle: "fade",
            autoPlay: 5000,
            slideSpeed: 700,
            singleItem: true,
            autoHeight: true,
            navigation: false,
            pagination: false,
            lazyLoad: true,
            addClassActive : true,
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Item carousel
        $(".item-carousel").owlCarousel({
            autoPlay: 3500,
            stopOnHover: false,
            items: 3,
            itemsDesktop: [1199, 3],
            itemsTabletSmall: [768, 3],
            itemsMobile: [480, 1],
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Small item carousel
        $(".small-item-carousel").owlCarousel({
            autoPlay: 2500,
            stopOnHover: true,
            items: 6,
            itemsDesktop: [1199, 4],
            itemsTabletSmall: [768, 3],
            itemsMobile: [480, 2],
            pagination: false,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Single carousel
        $(".single-carousel").owlCarousel({
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Content Slider
        $(".content-slider").owlCarousel({
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });

        // Photo slider
        $(".photo-slider").owlCarousel({
            slideSpeed: 350,
            items: 4,
            itemsDesktop: [1199, 4],
            itemsTabletSmall: [768, 2],
            itemsMobile: [480, 1],
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        }); 
        
        // Work slider
        $(".simple-slider").owlCarousel({
            slideSpeed : 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Work slider
        $(".work-full-slider").owlCarousel({
            slideSpeed : 350,
            singleItem: true,
            autoHeight: true,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ['<span class="sr-only">Previous Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5.005,28.500 L27.000,54.494 L24.000,56.994 L0.005,28.500 L24.000,0.006 L27.000,2.506 L5.005,28.500 Z"/></svg>', '<span class="sr-only">Next Slide</span><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="27px" height="57px" viewBox="0 0 27 57" fill="currentColor" aria-hidden="true" focusable="false"><path d="M21.995,28.500 L-0.000,54.494 L3.000,56.994 L26.995,28.500 L3.000,0.006 L-0.000,2.506 L21.995,28.500 Z"/></svg>'],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Blog posts carousel
        $(".blog-posts-carousel").owlCarousel({
            autoPlay: 5000,
            stopOnHover: true,
            items: 3,
            itemsDesktop: [1199, 3],
            itemsTabletSmall: [768, 2],
            itemsMobile: [480, 1],
            pagination: false,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Blog posts carousel alt
        $(".blog-posts-carousel-alt").owlCarousel({
            autoPlay: 3500,
            stopOnHover: true,
            slideSpeed: 350,
            singleItem: true,
            autoHeight: true,
            pagination: false,
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        });
        
        // Image carousel
        $(".image-carousel").owlCarousel({
            autoPlay: 5000,
            stopOnHover: true,
            items: 4,
            itemsDesktop: [1199, 3],
            itemsTabletSmall: [768, 2],
            itemsMobile: [480, 1],
            navigation: true,
            lazyLoad: true,
            addClassActive : true,
            navigationText: ["<span class='sr-only'>Previous Slide</span><i class='fa fa-angle-left' aria-hidden='true'></i>", "<span class='sr-only'>Next Slide</span><i class='fa fa-angle-right' aria-hidden='true'></i>"],
            afterInit: owl_keynav,
            afterAction: owl_update
        });        

    })(jQuery);
};


/* ---------------------------------------------
 Portfolio section
 --------------------------------------------- */

// Projects filtering

var fselector = 0;
var work_grid = $("#work-grid, #isotope");

function initWorkFilter(){
    (function($){
     "use strict";
     var isotope_mode;
     if (work_grid.hasClass("masonry")){
         isotope_mode = "masonry";
     } else{
         isotope_mode = "fitRows"
     }
     
     $(".filter").click(function(){         
         $(".filter").removeClass("active").attr("aria-pressed", "false");
         $(this).addClass("active").attr("aria-pressed", "true");
         fselector = $(this).attr("data-filter");
         var transition_duration = "0.4s";
         if (($("body").hasClass("appear-animate")) && (!($("html").hasClass("mobile")) && (work_grid.find(".wow-p").length))){
             transition_duration = 0;
         }
         work_grid.imagesLoaded(function(){
             work_grid.isotope({
                 itemSelector: ".mix",
                 layoutMode: isotope_mode,
                 filter: fselector,
                 transitionDuration: transition_duration
             });
         });        
         
         if ($("body").hasClass("appear-animate")) {
             var wow_p = new WOW({
                 boxClass: "wow-p",
                 animateClass: "animated",
                 offset: 100,
                 mobile: false,
                 live: true,
                 callback: function(box){
                     setInterval(function(){
                         $(box).removeClass("no-animate");
                     }, 1500);
                 }
             });
             wow_p.init();
         }           
         
         return false;
     });
        
     if (window.location.hash) {
         $(".filter").each(function(){
             if ($(this).attr("data-filter") == "." + window.location.hash.replace("#", "")) {
                 $(this).trigger("click");                                  
                 if ($("#portfolio").length) {
                     $("html, body").animate({
                         scrollTop: $("#portfolio").offset().top
                     });
                 }
                 
             }
         });
     }

     work_grid.imagesLoaded(function(){
         work_grid.isotope({
             itemSelector: ".mix",
             layoutMode: isotope_mode,
             filter: fselector
         });
     });
     
     // Lazy loading plus isotope filter
     
     $(".img-lazy-work").on("load", function(){
         masonry_update();
     });     
     function masonry_update(){
         work_grid.imagesLoaded(function(){
             work_grid.isotope({
                 itemSelector: ".mix",
                 layoutMode: isotope_mode,
                 filter: fselector
             });
         });
     }
     work_grid.on("arrangeComplete", function(){
         $(window).trigger("scroll");
     });
    
    })(jQuery);
}


/* ---------------------------------------------
 Google map
 --------------------------------------------- */

function init_map(){
    (function($){
        
        $(".map-section").click(function(){
            $(this).toggleClass("js-active");
            $(this).find(".mt-open").toggle();
            $(this).find(".mt-close").toggle();
            return false;
        });

    })(jQuery);
}


/* ---------------------------------------------
 HTML5 background video
 --------------------------------------------- */

function init_bg_video(){
    (function($){
        
        $(".bg-video-button-muted").click(function(){
        if ($(this).prev().find(".bg-video").prop('muted')) {
            $(this).prev().find(".bg-video").prop('muted', false);
            $(this).find("i").removeClass("fa-volume-off").addClass("fa-volume-up");
        }
        else {
            $(this).prev().find(".bg-video").prop('muted', true);
            $(this).find("i").removeClass("fa-volume-up").addClass("fa-volume-off");
        }
        
        return false;
    });

    })(jQuery);
}


/* ---------------------------------------------
 WOW animations
 --------------------------------------------- */

function init_wow(){
    (function($){    
        
        /* Wow init */
       
        if ($("body").hasClass("appear-animate")) {
            $(".wow").addClass("no-animate");
        }
        var wow = new WOW({
            boxClass: 'wow',
            animateClass: 'animated',
            offset: 100,
            mobile: false, 
            live: true,
            callback: function(box){                
                setInterval(function(){ $(box).removeClass("no-animate"); }, 1500);
            }
        });
        
        if ($("body").hasClass("appear-animate")){
           wow.init();            
        } else{
            $(".wow").css("opacity", "1");
        }
        
        /* Wow for portfolio init */
       
       if ($("body").hasClass("appear-animate")) {
            $(".wow-p").addClass("no-animate");
        }
        var wow_p = new WOW({
            boxClass: 'wow-p',
            animateClass: 'animated',
            offset: 100,
            mobile: false, 
            live: true,
            callback: function(box){                
                setInterval(function(){ $(box).removeClass("no-animate"); }, 1500);
            }
        });
        
        if ($("body").hasClass("appear-animate")){
           wow_p.init();            
        } else{
            $(".wow-p").css("opacity", "1");
        }
        
        /* Wow for menu bar init */
        
        if (($("body").hasClass("appear-animate")) && ($(window).width() >= 1024) && ($("html").hasClass("no-mobile"))){
           $(".wow-menubar").addClass("no-animate").addClass("fadeInDownShort").addClass("animated");  
           setInterval(function(){ $(".wow-menubar").removeClass("no-animate"); }, 1500);         
        } else{
            $(".wow-menubar").css("opacity", "1");
        }
        
    })(jQuery);
}


/* ---------------------------------------------
 Masonry
 --------------------------------------------- */

function init_masonry(){
    (function($){    
    
        $(".masonry").imagesLoaded(function(){
            $(".masonry").masonry();
        });
        
    })(jQuery);
}


/* ---------------------------------------------
 Polyfill for :focus-visible     
 --------------------------------------------- */

/**
 * https://github.com/WICG/focus-visible
 */
function init() {
  var hadKeyboardEvent = true;
  var hadFocusVisibleRecently = false;
  var hadFocusVisibleRecentlyTimeout = null;

  var inputTypesWhitelist = {
    text: true,
    search: true,
    url: true,
    tel: true,
    email: true,
    password: true,
    number: true,
    date: true,
    month: true,
    week: true,
    time: true,
    datetime: true,
    'datetime-local': true
  };

  /**
   * Helper function for legacy browsers and iframes which sometimes focus
   * elements like document, body, and non-interactive SVG.
   * @param {Element} el
   */
  function isValidFocusTarget(el) {
    if (
      el &&
      el !== document &&
      el.nodeName !== 'HTML' &&
      el.nodeName !== 'BODY' &&
      'classList' in el &&
      'contains' in el.classList
    ) {
      return true;
    }
    return false;
  }

  /**
   * Computes whether the given element should automatically trigger the
   * `focus-visible` class being added, i.e. whether it should always match
   * `:focus-visible` when focused.
   * @param {Element} el
   * @return {boolean}
   */
  function focusTriggersKeyboardModality(el) {
    var type = el.type;
    var tagName = el.tagName;

    if (tagName == 'INPUT' && inputTypesWhitelist[type] && !el.readOnly) {
      return true;
    }

    if (tagName == 'TEXTAREA' && !el.readOnly) {
      return true;
    }

    if (el.isContentEditable) {
      return true;
    }

    return false;
  }

  /**
   * Add the `focus-visible` class to the given element if it was not added by
   * the author.
   * @param {Element} el
   */
  function addFocusVisibleClass(el) {
    if (el.classList.contains('focus-visible')) {
      return;
    }
    el.classList.add('focus-visible');
    el.setAttribute('data-focus-visible-added', '');
  }

  /**
   * Remove the `focus-visible` class from the given element if it was not
   * originally added by the author.
   * @param {Element} el
   */
  function removeFocusVisibleClass(el) {
    if (!el.hasAttribute('data-focus-visible-added')) {
      return;
    }
    el.classList.remove('focus-visible');
    el.removeAttribute('data-focus-visible-added');
  }

  /**
   * Treat `keydown` as a signal that the user is in keyboard modality.
   * Apply `focus-visible` to any current active element and keep track
   * of our keyboard modality state with `hadKeyboardEvent`.
   * @param {Event} e
   */
  function onKeyDown(e) {
    if (isValidFocusTarget(document.activeElement)) {
      addFocusVisibleClass(document.activeElement);
    }

    hadKeyboardEvent = true;
  }

  /**
   * If at any point a user clicks with a pointing device, ensure that we change
   * the modality away from keyboard.
   * This avoids the situation where a user presses a key on an already focused
   * element, and then clicks on a different element, focusing it with a
   * pointing device, while we still think we're in keyboard modality.
   * @param {Event} e
   */
  function onPointerDown(e) {
    hadKeyboardEvent = false;
  }

  /**
   * On `focus`, add the `focus-visible` class to the target if:
   * - the target received focus as a result of keyboard navigation, or
   * - the event target is an element that will likely require interaction
   *   via the keyboard (e.g. a text box)
   * @param {Event} e
   */
  function onFocus(e) {
    // Prevent IE from focusing the document or HTML element.
    if (!isValidFocusTarget(e.target)) {
      return;
    }

    if (hadKeyboardEvent || focusTriggersKeyboardModality(e.target)) {
      addFocusVisibleClass(e.target);
    }
  }

  /**
   * On `blur`, remove the `focus-visible` class from the target.
   * @param {Event} e
   */
  function onBlur(e) {
    if (!isValidFocusTarget(e.target)) {
      return;
    }

    if (
      e.target.classList.contains('focus-visible') ||
      e.target.hasAttribute('data-focus-visible-added')
    ) {
      // To detect a tab/window switch, we look for a blur event followed
      // rapidly by a visibility change.
      // If we don't see a visibility change within 100ms, it's probably a
      // regular focus change.
      hadFocusVisibleRecently = true;
      window.clearTimeout(hadFocusVisibleRecentlyTimeout);
      hadFocusVisibleRecentlyTimeout = window.setTimeout(function() {
        hadFocusVisibleRecently = false;
        window.clearTimeout(hadFocusVisibleRecentlyTimeout);
      }, 100);
      removeFocusVisibleClass(e.target);
    }
  }

  /**
   * If the user changes tabs, keep track of whether or not the previously
   * focused element had .focus-visible.
   * @param {Event} e
   */
  function onVisibilityChange(e) {
    if (document.visibilityState == 'hidden') {
      // If the tab becomes active again, the browser will handle calling focus
      // on the element (Safari actually calls it twice).
      // If this tab change caused a blur on an element with focus-visible,
      // re-apply the class when the user switches back to the tab.
      if (hadFocusVisibleRecently) {
        hadKeyboardEvent = true;
      }
      addInitialPointerMoveListeners();
    }
  }

  /**
   * Add a group of listeners to detect usage of any pointing devices.
   * These listeners will be added when the polyfill first loads, and anytime
   * the window is blurred, so that they are active when the window regains
   * focus.
   */
  function addInitialPointerMoveListeners() {
    document.addEventListener('mousemove', onInitialPointerMove);
    document.addEventListener('mousedown', onInitialPointerMove);
    document.addEventListener('mouseup', onInitialPointerMove);
    document.addEventListener('pointermove', onInitialPointerMove);
    document.addEventListener('pointerdown', onInitialPointerMove);
    document.addEventListener('pointerup', onInitialPointerMove);
    document.addEventListener('touchmove', onInitialPointerMove);
    document.addEventListener('touchstart', onInitialPointerMove);
    document.addEventListener('touchend', onInitialPointerMove);
  }

  function removeInitialPointerMoveListeners() {
    document.removeEventListener('mousemove', onInitialPointerMove);
    document.removeEventListener('mousedown', onInitialPointerMove);
    document.removeEventListener('mouseup', onInitialPointerMove);
    document.removeEventListener('pointermove', onInitialPointerMove);
    document.removeEventListener('pointerdown', onInitialPointerMove);
    document.removeEventListener('pointerup', onInitialPointerMove);
    document.removeEventListener('touchmove', onInitialPointerMove);
    document.removeEventListener('touchstart', onInitialPointerMove);
    document.removeEventListener('touchend', onInitialPointerMove);
  }

  /**
   * When the polfyill first loads, assume the user is in keyboard modality.
   * If any event is received from a pointing device (e.g. mouse, pointer,
   * touch), turn off keyboard modality.
   * This accounts for situations where focus enters the page from the URL bar.
   * @param {Event} e
   */
  function onInitialPointerMove(e) {
    // Work around a Safari quirk that fires a mousemove on <html> whenever the
    // window blurs, even if you're tabbing out of the page. ¯\_(ツ)_/¯
    if (e.target.nodeName.toLowerCase() === 'html') {
      return;
    }

    hadKeyboardEvent = false;
    removeInitialPointerMoveListeners();
  }

  document.addEventListener('keydown', onKeyDown, true);
  document.addEventListener('mousedown', onPointerDown, true);
  document.addEventListener('pointerdown', onPointerDown, true);
  document.addEventListener('touchstart', onPointerDown, true);
  document.addEventListener('focus', onFocus, true);
  document.addEventListener('blur', onBlur, true);
  document.addEventListener('visibilitychange', onVisibilityChange, true);
  addInitialPointerMoveListeners();

  document.body.classList.add('js-focus-visible');
}

/**
 * Subscription when the DOM is ready
 * @param {Function} callback
 */
function onDOMReady(callback) {
  var loaded;

  /**
   * Callback wrapper for check loaded state
   */
  function load() {
    if (!loaded) {
      loaded = true;

      callback();
    }
  }

  if (['interactive', 'complete'].indexOf(document.readyState) >= 0) {
    callback();
  } else {
    loaded = false;
    document.addEventListener('DOMContentLoaded', load, false);
    window.addEventListener('load', load, false);
  }
}

if (typeof document !== 'undefined') {
  onDOMReady(init);
}


/* ---------------------------------------------
 Adding aria-hidden to Font Awesome 
 icons
 --------------------------------------------- */

(function(){
    let getIcons = document.querySelectorAll('i.fa, i.fab, i.far, i.fas');
    getIcons.forEach(function(iconEach)
    {
        let getIconAttr = iconEach.getAttribute('aria-hidden');
        if (!getIconAttr)
        {
            iconEach.setAttribute('aria-hidden','true');
        }
    });
})();