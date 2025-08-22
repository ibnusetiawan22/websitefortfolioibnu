/*================== toggle icon navbar ==========================*/
let menuIcon = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

menuIcon.onclick = () => {
    menuIcon.classList.toggle('bx-x');
    navbar.classList.toggle('active');
};

/*================== scroll sections active link ==========================*/
let sections = document.querySelectorAll('section');
let navlinks = document.querySelectorAll('header nav a');

window.onscroll = () => {
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if(top>= offset && top < offset + height) {
            navlinks.forEach(link => {
                link.classList.remove('active');
                document.querySelector('header nav a[href*='+ id +']').classList.add('active')
            });
        
        };
    });


   /*================== sticky navbar ==========================*/
   let header = document.querySelector('header');

   header.classList.toggle('sticky' , window.scrollY > 100);

   /*================== ewmove toogle icon navbar ==========================*/
   menuIcon.classList.remove('bx-x');
   navbar.classList.remove('active');
};



ScrollReveal({
    distance: '80px',
    duration: 2000,
    delay: 200
});

ScrollReveal().reveal('.home-content, .heading', { origin: 'top' });
ScrollReveal().reveal('.home-img, .services-container, .portfolio-box, .contact form', { origin: 'bottom' });
ScrollReveal().reveal('.home-content h1, .about-img', { origin: 'left' });
ScrollReveal().reveal('.home-content p, .about-content', { origin: 'right' });

/*================== typed js  ==========================*/

const typed = new Typed('.multiple-text',{
    strings: ['Junior Web Developer','Junior Network Administrator','Junior Desain Graphic'],
    typeSpeed: 100,
    backSpeed: 100,
    backDelay: 1000,
    loop: true

});


document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
      card.classList.add('show');
    });
  });
  
