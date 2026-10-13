import os
import sys
import shutil
from pathlib import Path
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings

from apps.catalog.models import (
    Category, Brand, Size, Colour, Product, ProductImage,
    ProductVariant, Inventory, HomeBanner
)
from apps.accounts.models import Address
from apps.cart.models import Coupon, Cart, CartItem
from apps.orders.models import Order, OrderItem

User = get_user_model()

# Exact 36 catalog products sourced from Fashion Product Images dataset
FASHION_DATASET_36 = [
    # ------------------ 1. WOMEN'S CLOTHING (6) ------------------
    {
        'id': 39716,
        'title': 'Arrow Woman Women Blue Dress',
        'category_slug': 'womens-clothing',
        'brand': 'Arrow Woman',
        'gender': 'women',
        'colour': 'Navy Blue',
        'hex': '#1B2A4A',
        'base_price': Decimal('3999.00'),
        'discount_price': Decimal('3299.00'),
        'is_featured': True,
        'is_new_arrival': True,
        'sizes': ['XS', 'S', 'M', 'L', 'XL'],
        'description': 'Architecturally tailored navy blue shift dress featuring a jewel neckline, subtle darting for contour, and an elegant concealed back zip closure. Crafted from structured stretch crepe.'
    },
    {
        'id': 49653,
        'title': 'Mineral Women Green Top',
        'category_slug': 'womens-clothing',
        'brand': 'Mineral',
        'gender': 'women',
        'colour': 'Emerald Green',
        'hex': '#1B4D3E',
        'base_price': Decimal('1899.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['XS', 'S', 'M', 'L'],
        'description': 'Contemporary draped silhouette top in an earthy green hue with an asymmetrical fluid hemline and cap sleeves. Cut from lightweight breathable viscose fabric.'
    },
    {
        'id': 26960,
        'title': 'Jealous 21 Women Purple Shirt',
        'category_slug': 'womens-clothing',
        'brand': 'Jealous 21',
        'gender': 'women',
        'colour': 'Purple',
        'hex': '#582A72',
        'base_price': Decimal('2199.00'),
        'discount_price': Decimal('1699.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L'],
        'description': 'Crisp collared woven shirt in a deep amethyst purple, featuring clean tonal buttons, tailored single-button cuffs, and a curved hemline.'
    },
    {
        'id': 20099,
        'title': 'Diva Women Embroided Green Kurta',
        'category_slug': 'womens-clothing',
        'brand': 'Diva',
        'gender': 'women',
        'colour': 'Forest Green',
        'hex': '#22553B',
        'base_price': Decimal('3499.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Artisanal long tunic kurta in forest green featuring intricate tonal thread embroidery along the mandarin collar and front placket. Styled with three-quarter sleeves.'
    },
    {
        'id': 26994,
        'title': 'Jealous 21 Women Black Jeans',
        'category_slug': 'womens-clothing',
        'brand': 'Jealous 21',
        'gender': 'women',
        'colour': 'Charcoal Black',
        'hex': '#1E1E1E',
        'base_price': Decimal('2899.00'),
        'discount_price': Decimal('2399.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['XS', 'S', 'M', 'L'],
        'description': 'Mid-rise slim-fit jeans in deep obsidian black denim, spun with subtle stretch for all-day comfort and shape retention. Finished with classic five-pocket styling.'
    },
    {
        'id': 2288,
        'title': 'Nike Women Black T-shirt',
        'category_slug': 'womens-clothing',
        'brand': 'Nike',
        'gender': 'women',
        'colour': 'Jet Black',
        'hex': '#111111',
        'base_price': Decimal('1799.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['XS', 'S', 'M', 'L', 'XL'],
        'description': 'Performance knit essential tee engineered from breathable cotton-jersey with tonal athletic flatlock seams and the signature swoosh emblem at the chest.'
    },

    # ------------------ 2. MEN'S CLOTHING (6) ------------------
    {
        'id': 15970,
        'title': 'Turtle Check Men Navy Blue Shirt',
        'category_slug': 'mens-clothing',
        'brand': 'Turtle',
        'gender': 'men',
        'colour': 'Navy Blue',
        'hex': '#1B2A4A',
        'base_price': Decimal('2499.00'),
        'discount_price': Decimal('1999.00'),
        'is_featured': True,
        'is_new_arrival': True,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Tailored button-down oxford shirt featuring an understated navy and white micro-check pattern. Woven from 100% fine cotton yarn with mother-of-pearl buttons.'
    },
    {
        'id': 39386,
        'title': 'Peter England Men Party Blue Jeans',
        'category_slug': 'mens-clothing',
        'brand': 'Peter England',
        'gender': 'men',
        'colour': 'Classic Blue',
        'hex': '#28587B',
        'base_price': Decimal('2799.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Contemporary straight-leg denim jeans in authentic indigo wash with whiskering details, contrast amber stitching, and reinforced belt loops.'
    },
    {
        'id': 13089,
        'title': 'ADIDAS Men Lfc Auth Hood Grey Sweatshirts',
        'category_slug': 'mens-clothing',
        'brand': 'ADIDAS',
        'gender': 'men',
        'colour': 'Heather Grey',
        'hex': '#7A7D81',
        'base_price': Decimal('4299.00'),
        'discount_price': Decimal('3699.00'),
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Athletic pullover hoodie crafted with cozy brushed cotton fleece interior, adjustable drawstring hood, kangaroo pouch pocket, and ribbed athletic cuffs.'
    },
    {
        'id': 53759,
        'title': 'Puma Men Grey T-shirt',
        'category_slug': 'mens-clothing',
        'brand': 'Puma',
        'gender': 'men',
        'colour': 'Light Grey',
        'hex': '#B8B9BB',
        'base_price': Decimal('1499.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Minimalist crewneck casual tee tailored from soft ring-spun jersey with taped neck seams and subtle Puma cat branding across the left chest.'
    },
    {
        'id': 30805,
        'title': 'Fabindia Men Striped Green Shirt',
        'category_slug': 'mens-clothing',
        'brand': 'Fabindia',
        'gender': 'men',
        'colour': 'Sage Green',
        'hex': '#607D67',
        'base_price': Decimal('2299.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Handwoven artisan shirt in organic sage green cotton with slender vertical woven stripes, patch chest pocket, and relaxed spread collar.'
    },
    {
        'id': 7990,
        'title': "Fila Men's Round Neck Navy Blue T-shirt",
        'category_slug': 'mens-clothing',
        'brand': 'Fila',
        'gender': 'men',
        'colour': 'Navy Blue',
        'hex': '#1B2A4A',
        'base_price': Decimal('1399.00'),
        'discount_price': Decimal('1099.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['S', 'M', 'L', 'XL'],
        'description': 'Heritage athletic crewneck tee in deep navy blue, finished with soft ribbed collar trim and subtle contrast chest print.'
    },

    # ------------------ 3. SHOES (6) ------------------
    {
        'id': 9036,
        'title': 'Buckaroo Men Flores Black Formal Shoes',
        'category_slug': 'shoes',
        'brand': 'Buckaroo',
        'gender': 'men',
        'colour': 'Charcoal Black',
        'hex': '#1C1C1C',
        'base_price': Decimal('4999.00'),
        'discount_price': Decimal('4299.00'),
        'is_featured': True,
        'is_new_arrival': False,
        'sizes': ['UK 7', 'UK 8', 'UK 9', 'UK 10'],
        'description': 'Handcrafted derby lace-up formal shoes in polished full-grain black leather with brogue perimeter detailing, cushioned insoles, and stacked composite heels.'
    },
    {
        'id': 9204,
        'title': 'Puma Men Future Cat Remix SF Black Casual Shoes',
        'category_slug': 'shoes',
        'brand': 'Puma',
        'gender': 'men',
        'colour': 'Charcoal Black',
        'hex': '#222222',
        'base_price': Decimal('5499.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['UK 7', 'UK 8', 'UK 9', 'UK 10'],
        'description': 'Iconic aerodynamic motorsport sneakers featuring an asymmetric lacing system, rounded driver heel, soft leather upper, and Scuderia Ferrari emblem.'
    },
    {
        'id': 3168,
        'title': "Nike Men's Incinerate MSL White Blue Shoe",
        'category_slug': 'shoes',
        'brand': 'Nike',
        'gender': 'men',
        'colour': 'Chalk White',
        'hex': '#F4F4F6',
        'base_price': Decimal('4799.00'),
        'discount_price': Decimal('3999.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['UK 7', 'UK 8', 'UK 9', 'UK 10'],
        'description': 'Engineered running shoes combining breathable mesh panels, responsive phylon foam midsole cushioning, and deep flex grooves for natural stride dynamics.'
    },
    {
        'id': 59051,
        'title': 'Carlton London Women Black & Gold Toned Flats',
        'category_slug': 'shoes',
        'brand': 'Carlton London',
        'gender': 'women',
        'colour': 'Black & Gold',
        'hex': '#28261F',
        'base_price': Decimal('2699.00'),
        'discount_price': Decimal('2199.00'),
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['UK 5', 'UK 6', 'UK 7', 'UK 8'],
        'description': 'Chic pointed-toe slingback flats in polished black leather accented with brushed champagne-gold hardware and cushioned ergonomic footbed.'
    },
    {
        'id': 2886,
        'title': 'Catwalk Women Leather Brown Flats',
        'category_slug': 'shoes',
        'brand': 'Catwalk',
        'gender': 'women',
        'colour': 'Warm Tan',
        'hex': '#8D5B3A',
        'base_price': Decimal('2499.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['UK 5', 'UK 6', 'UK 7', 'UK 8'],
        'description': 'Artisanal cognac-brown handcrafted leather slide flats with interwoven strap detailing, supple footbed, and textured slip-resistant outsole.'
    },
    {
        'id': 39988,
        'title': 'Gas Men Europa White Shoes',
        'category_slug': 'shoes',
        'brand': 'Gas',
        'gender': 'men',
        'colour': 'Pure White',
        'hex': '#FFFFFF',
        'base_price': Decimal('4999.00'),
        'discount_price': Decimal('4199.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['UK 7', 'UK 8', 'UK 9', 'UK 10'],
        'description': 'Minimalist court silhouette sneakers in smooth white leather with subtle perforated quarter panels, tonal laces, and vulcanized rubber cupsole.'
    },

    # ------------------ 4. BAGS (6) ------------------
    {
        'id': 47957,
        'title': 'Murcia Women Blue Handbag',
        'category_slug': 'bags',
        'brand': 'Murcia',
        'gender': 'women',
        'colour': 'Royal Blue',
        'hex': '#1E3F78',
        'base_price': Decimal('4499.00'),
        'discount_price': Decimal('3799.00'),
        'is_featured': True,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Architectural structured top-handle handbag in cobalt blue textured leather with brushed metal hardware, dual carrying options, and protective base studs.'
    },
    {
        'id': 47359,
        'title': 'Baggit Women Brown Handbag',
        'category_slug': 'bags',
        'brand': 'Baggit',
        'gender': 'women',
        'colour': 'Saddle Brown',
        'hex': '#663B1D',
        'base_price': Decimal('3299.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Cruelty-free rich chestnut shoulder tote featuring spacious zippered compartments, internal organizer slots, and reinforced dual shoulder straps.'
    },
    {
        'id': 58183,
        'title': 'Rocky S Women White Handbag',
        'category_slug': 'bags',
        'brand': 'Rocky S',
        'gender': 'women',
        'colour': 'Ivory White',
        'hex': '#F2F1ED',
        'base_price': Decimal('5499.00'),
        'discount_price': Decimal('4699.00'),
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Designer satchel in pristine ivory featuring clean modernist lines, a fold-over magnetic closure, detachable crossbody strap, and engraved designer tag.'
    },
    {
        'id': 20851,
        'title': 'Spice Art Women Ribbon Embroidery Red Clutch',
        'category_slug': 'bags',
        'brand': 'Spice Art',
        'gender': 'women',
        'colour': 'Crimson Red',
        'hex': '#9E1B24',
        'base_price': Decimal('2799.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Handcrafted evening box clutch in rich ruby-red satin with floral silk ribbon embroidery, polished snap clasp, and a hideaway chain strap.'
    },
    {
        'id': 39524,
        'title': 'Peter England Unisex Orange Sleeve Bag',
        'category_slug': 'bags',
        'brand': 'Peter England',
        'gender': 'unisex',
        'colour': 'Burnt Orange',
        'hex': '#C85A17',
        'base_price': Decimal('1999.00'),
        'discount_price': Decimal('1499.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Slim urban tech folio sleeve in high-visibility heritage orange with shock-absorbing foam padding, water-resistant exterior, and plush microfleece lining.'
    },
    {
        'id': 12732,
        'title': 'Nike Unisex Swoosh Black Backpack',
        'category_slug': 'bags',
        'brand': 'Nike',
        'gender': 'unisex',
        'colour': 'Charcoal Black',
        'hex': '#1A1A1A',
        'base_price': Decimal('2999.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Commuter backpack in durable matte black polyester twill with dual-zip main compartment, exterior zippered front pocket, and padded mesh shoulder straps.'
    },

    # ------------------ 5. JEWELLERY (6) ------------------
    {
        'id': 48781,
        'title': 'Lucera Women Silver Pendant',
        'category_slug': 'jewellery',
        'brand': 'Lucera',
        'gender': 'women',
        'colour': 'Sterling Silver',
        'hex': '#D4D7DF',
        'base_price': Decimal('2899.00'),
        'discount_price': Decimal('2299.00'),
        'is_featured': True,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Solid 925 sterling silver sculpted pendant inspired by fluid molten drops, suspended from a delicate 18-inch diamond-cut cable chain with spring clasp.'
    },
    {
        'id': 49005,
        'title': 'Lucera Women Silver Ring',
        'category_slug': 'jewellery',
        'brand': 'Lucera',
        'gender': 'women',
        'colour': 'Sterling Silver',
        'hex': '#D4D7DF',
        'base_price': Decimal('1899.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Minimalist comfort-fit band ring cast in fine sterling silver with a softly burnished satin finish, designed for versatile everyday stacking.'
    },
    {
        'id': 35322,
        'title': 'Fabindia Women Anusuya Silver Earrings',
        'category_slug': 'jewellery',
        'brand': 'Fabindia',
        'gender': 'women',
        'colour': 'Antique Silver',
        'hex': '#A0A4A8',
        'base_price': Decimal('2499.00'),
        'discount_price': Decimal('1999.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Traditional filigree drop earrings hand-cast in pure oxidised sterling silver featuring floral lotus motifs and gentle bell ghungroo accents.'
    },
    {
        'id': 56214,
        'title': 'Estelle Women Gold Earrings',
        'category_slug': 'jewellery',
        'brand': 'Estelle',
        'gender': 'women',
        'colour': 'Champagne Gold',
        'hex': '#D9B44A',
        'base_price': Decimal('2199.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Sculptural huggie hoop earrings finished in rich 18K yellow gold vermeil with a high-shine mirror polish and secure snap-bar backing.'
    },
    {
        'id': 48311,
        'title': 'Pitaraa Women Bronze Beaded Bracelet',
        'category_slug': 'jewellery',
        'brand': 'Pitaraa',
        'gender': 'women',
        'colour': 'Antique Bronze',
        'hex': '#7A5230',
        'base_price': Decimal('1599.00'),
        'discount_price': Decimal('1299.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Multi-strand artisanal beaded bracelet combining hand-cut faceted metallic bronze beads with braided thread cords and an adjustable drawstring closure.'
    },
    {
        'id': 52224,
        'title': 'Lencia Grey Swarovski Pearl Necklace',
        'category_slug': 'jewellery',
        'brand': 'Lencia',
        'gender': 'women',
        'colour': 'Lustrous Pearl',
        'hex': '#E8E8EE',
        'base_price': Decimal('4899.00'),
        'discount_price': Decimal('3999.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Graduated strand necklace hand-knotted with iridescent grey Swarovski simulated pearls and secured with a 925 sterling silver filigree fishhook clasp.'
    },

    # ------------------ 6. ACCESSORIES (6) ------------------
    {
        'id': 25947,
        'title': 'Femella Women Brown Scarf',
        'category_slug': 'accessories',
        'brand': 'Femella',
        'gender': 'women',
        'colour': 'Warm Brown',
        'hex': '#6F4E37',
        'base_price': Decimal('1499.00'),
        'discount_price': Decimal('1199.00'),
        'is_featured': True,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Ultra-soft woven autumn wrap scarf in rich espresso brown with fine eyelash fringed edges and generous drape for effortless layering.'
    },
    {
        'id': 16957,
        'title': 'Image Men Sunglasses',
        'category_slug': 'accessories',
        'brand': 'Image',
        'gender': 'men',
        'colour': 'Matte Black',
        'hex': '#222222',
        'base_price': Decimal('2999.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': True,
        'sizes': ['One Size'],
        'description': 'Wayfarer-inspired square sunglasses handcrafted with durable matte black acetate frames, stainless-steel five-barrel hinges, and 100% UV400 protective polarized lenses.'
    },
    {
        'id': 59263,
        'title': 'Titan Women Silver Watch',
        'category_slug': 'accessories',
        'brand': 'Titan',
        'gender': 'women',
        'colour': 'Sterling Silver',
        'hex': '#C5C6D0',
        'base_price': Decimal('5999.00'),
        'discount_price': Decimal('4999.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Sculptural stainless-steel dress watch featuring a shimmering sunray silver dial, minimalist metallic indices, mineral crystal lens, and solid link bracelet.'
    },
    {
        'id': 17429,
        'title': 'CASIO G-Shock Men Black Digital Watch G-7710-1DR G223',
        'category_slug': 'accessories',
        'brand': 'CASIO',
        'gender': 'men',
        'colour': 'Stealth Black',
        'hex': '#1B1B1B',
        'base_price': Decimal('6495.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Heavy-duty shock-resistant tactical timepiece in stealth matte black resin, offering 200m water resistance, world time in 48 cities, dual 1/1000s stopwatches, and auto-LED backlight.'
    },
    {
        'id': 48123,
        'title': 'Fossil Women Black Huarache Weave Belt',
        'category_slug': 'accessories',
        'brand': 'Fossil',
        'gender': 'women',
        'colour': 'Charcoal Black',
        'hex': '#242424',
        'base_price': Decimal('2499.00'),
        'discount_price': Decimal('1999.00'),
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Artisanal hand-braided huarache leather belt in rich matte black cowhide, finished with a gently brushed antique brass single-prong roller buckle.'
    },
    {
        'id': 18839,
        'title': 'Peter England Men Formal Black Belt',
        'category_slug': 'accessories',
        'brand': 'Peter England',
        'gender': 'men',
        'colour': 'Charcoal Black',
        'hex': '#181818',
        'base_price': Decimal('1699.00'),
        'discount_price': None,
        'is_featured': False,
        'is_new_arrival': False,
        'sizes': ['One Size'],
        'description': 'Executive dress belt crafted from smooth full-grain black bridle leather with feather-stitched edges and a polished nickel harness buckle.'
    },
]


class Command(BaseCommand):
    help = 'Seeds Supabase PostgreSQL with the authoritative 36-product Fashion Product Images dataset catalog'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Updating LumaCart catalog to authoritative 36-product Fashion dataset...'))

        media_products_dir = Path(settings.MEDIA_ROOT) / 'products'
        media_products_dir.mkdir(parents=True, exist_ok=True)

        with transaction.atomic():
            # 1. Ensure Superuser & Demo Customer
            admin_user, _ = User.objects.get_or_create(
                email='admin@lumacart.com',
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'LumaCart',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_email_verified': True,
                    'phone_number': '+91 98765 43210'
                }
            )
            if not admin_user.has_usable_password():
                admin_user.set_password('Admin@12345')
                admin_user.save()

            demo_user, _ = User.objects.get_or_create(
                email='customer@lumacart.com',
                defaults={
                    'first_name': 'Sophia',
                    'last_name': 'Kapoor',
                    'is_staff': False,
                    'is_email_verified': True,
                    'phone_number': '+91 98111 22334'
                }
            )
            if not demo_user.has_usable_password():
                demo_user.set_password('Customer@12345')
                demo_user.save()

            Address.objects.get_or_create(
                user=demo_user,
                is_default=True,
                defaults={
                    'full_name': 'Sophia Kapoor',
                    'phone_number': '+91 98111 22334',
                    'street_address': 'Flat 402, Lotus Grand Residences, Indiranagar 100ft Road',
                    'landmark': 'Opposite Defense Colony Park',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'postal_code': '560038',
                    'country': 'India',
                    'address_type': 'both'
                }
            )

            # 2. Categories: The 6 exact categories
            categories_data = [
                {
                    'name': "Women's Clothing",
                    'slug': 'womens-clothing',
                    'description': 'Tailored dresses, fluid tops, artisan kurtas, crisp shirts, and designer jeans.'
                },
                {
                    'name': "Men's Clothing",
                    'slug': 'mens-clothing',
                    'description': 'Oxford button-down shirts, selvedge denim jeans, athletic hoodies, and everyday jersey tees.'
                },
                {
                    'name': 'Shoes',
                    'slug': 'shoes',
                    'description': 'Handcrafted leather derby shoes, motorsport sneakers, performance trainers, and slingback flats.'
                },
                {
                    'name': 'Bags',
                    'slug': 'bags',
                    'description': 'Structured leather top-handle satchels, artisanal clutches, tech folios, and commuter backpacks.'
                },
                {
                    'name': 'Jewellery',
                    'slug': 'jewellery',
                    'description': 'Solid 925 sterling silver pendants, stackable band rings, gold huggie hoops, and Swarovski pearl necklaces.'
                },
                {
                    'name': 'Accessories',
                    'slug': 'accessories',
                    'description': 'Woven autumn scarves, polarized acetate sunglasses, stainless-steel timepieces, and bridle leather belts.'
                },
            ]
            categories = {}
            for i, cat in enumerate(categories_data):
                obj, _ = Category.objects.update_or_create(
                    slug=cat['slug'],
                    defaults={'name': cat['name'], 'description': cat['description'], 'display_order': i, 'is_active': True}
                )
                categories[cat['slug']] = obj

            # Also ensure legacy category slug exists so any old references resolve
            Category.objects.get_or_create(
                slug='jewelry-and-accessories',
                defaults={'name': 'Jewelry & Accessories', 'display_order': 10, 'is_active': True}
            )

            # 3. Sizes
            size_names = ['XS', 'S', 'M', 'L', 'XL', 'UK 5', 'UK 6', 'UK 7', 'UK 8', 'UK 9', 'UK 10', 'One Size']
            sizes = {}
            for i, name in enumerate(size_names):
                obj, _ = Size.objects.get_or_create(name=name, defaults={'sort_order': i})
                sizes[name] = obj

            # 4. Colours
            colours = {}
            for p_info in FASHION_DATASET_36:
                cname = p_info['colour']
                chex = p_info['hex']
                obj, _ = Colour.objects.get_or_create(name=cname, defaults={'hex_code': chex})
                colours[cname] = obj

            # 5. Coupons
            Coupon.objects.get_or_create(
                code='WELCOME10',
                defaults={
                    'discount_type': 'percentage',
                    'discount_value': Decimal('10.00'),
                    'min_purchase': Decimal('1000.00'),
                    'max_discount': Decimal('1500.00'),
                    'valid_to': timezone.now() + timezone.timedelta(days=365),
                    'is_active': True
                }
            )
            Coupon.objects.get_or_create(
                code='FASHION20',
                defaults={
                    'discount_type': 'percentage',
                    'discount_value': Decimal('20.00'),
                    'min_purchase': Decimal('3000.00'),
                    'max_discount': Decimal('3000.00'),
                    'valid_to': timezone.now() + timezone.timedelta(days=180),
                    'is_active': True
                }
            )

            # 6. Clean up old orders/carts so foreign key constraints do not block synchronization
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            CartItem.objects.all().delete()
            Cart.objects.all().delete()

            # Identify target 36 IDs
            target_ids = {p['id'] for p in FASHION_DATASET_36}

            # Delete any existing products not in target 36 IDs
            stale_products = Product.objects.exclude(id__in=target_ids)
            stale_count = stale_products.count()
            if stale_count > 0:
                self.stdout.write(f'Removing {stale_count} legacy/duplicate products not in the authoritative catalog...')
                stale_products.delete()

            # 7. Seed/Update the 36 products
            self.stdout.write(f'Seeding {len(FASHION_DATASET_36)} authoritative products...')

            for item in FASHION_DATASET_36:
                pid = item['id']
                cat = categories[item['category_slug']]
                brand_obj, _ = Brand.objects.get_or_create(name=item['brand'])

                product_slug = slugify(f"{item['title']}-{pid}")

                product, created = Product.objects.update_or_create(
                    id=pid,
                    defaults={
                        'title': item['title'],
                        'slug': product_slug,
                        'category': cat,
                        'brand': brand_obj,
                        'description': item['description'],
                        'gender': item['gender'],
                        'base_price': item['base_price'],
                        'discount_price': item['discount_price'],
                        'is_featured': item['is_featured'],
                        'is_new_arrival': item['is_new_arrival'],
                        'is_active': True,
                    }
                )

                # Images
                local_rel_path = f"products/{pid}.jpg"
                full_local_path = settings.MEDIA_ROOT / local_rel_path

                if not full_local_path.exists():
                    self.stdout.write(self.style.WARNING(f"Warning: Image file {full_local_path} not found!"))

                # Ensure ProductImage
                ProductImage.objects.filter(product=product).delete()
                ProductImage.objects.create(
                    product=product,
                    image=local_rel_path,
                    image_url=f"/media/{local_rel_path}",
                    alt_text=item['title'],
                    is_primary=True,
                    display_order=0
                )

                # Variants & Inventory
                item_colour = colours[item['colour']]
                for sz_name in item['sizes']:
                    sz_obj = sizes[sz_name]
                    sku = f"LMC-{pid}-{sz_name.replace(' ', '')}"
                    variant, _ = ProductVariant.objects.update_or_create(
                        product=product,
                        size=sz_obj,
                        colour=item_colour,
                        defaults={
                            'sku': sku,
                            'is_active': True
                        }
                    )
                    Inventory.objects.update_or_create(
                        variant=variant,
                        defaults={
                            'stock_quantity': 35,
                            'reserved_quantity': 0,
                            'low_stock_threshold': 5
                        }
                    )

            # 8. Home Banner
            HomeBanner.objects.all().delete()
            HomeBanner.objects.create(
                title="LumaCart",
                subtitle="Your Shopping Platform",
                badge_text="2026 COLLECTION",
                button_text="Shop The Catalog",
                link_url="/pages/products.html",
                is_active=True,
                display_order=0
            )

        total_in_db = Product.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f'Successfully synced LumaCart catalog! Total active products in Supabase: {total_in_db}'))
