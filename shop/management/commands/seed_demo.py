from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Category, Product
from workouts.models import Exercise

CATEGORIES = [
    ("Strength & Weights", "strength-weights", "Dumbbells, barbells, kettlebells and benches for building strength."),
    ("Cardio & Conditioning", "cardio-conditioning", "Skipping ropes, bands, mats and gear for fat loss and stamina."),
    ("Yoga & Recovery", "yoga-recovery", "Mats, foam rollers and stretch gear for mobility and recovery."),
    ("Cricket", "cricket", "Bats, balls and protective gear for the nets and the match."),
    ("Badminton & Racket Sports", "badminton-racket-sports", "Rackets, shuttles and court essentials."),
    ("Footwear & Apparel", "footwear-apparel", "Training shoes and breathable sportswear."),
    ("Gym Accessories", "gym-accessories", "Gloves, belts, bottles and bags for every session."),
]

# (category slug, name, brand, MRP, sale price or None, stock, short description, featured)
PRODUCTS = [
    ("strength-weights", "Adjustable Dumbbell Set 20 kg", "IronCore", 4999, 3999, 25, "Chrome-plated plates with a spin-lock bar for 2–20 kg loads.", True),
    ("strength-weights", "Rubber Hex Dumbbell Pair 5 kg", "IronCore", 1799, 1499, 40, "Anti-roll hex heads with a knurled steel handle.", False),
    ("strength-weights", "Cast Iron Kettlebell 12 kg", "IronCore", 2199, 1899, 18, "Wide handle, flat base, powder-coated finish.", True),
    ("strength-weights", "Olympic Barbell 7 ft", "IronCore", 8499, None, 6, "Rated for heavy lifting with bronze bushings and medium knurl.", False),
    ("strength-weights", "Flat-Incline Adjustable Bench", "FlexPro", 7999, 6499, 9, "Seven back positions with a 300 kg load rating.", False),
    ("strength-weights", "Pull-up Bar (Doorway)", "FlexPro", 1299, 999, 32, "No-screw doorway mount with multiple grips.", False),
    ("cardio-conditioning", "Speed Skipping Rope", "SprintLab", 499, 349, 80, "Ball-bearing handles with an adjustable steel cable.", True),
    ("cardio-conditioning", "Resistance Band Set (5 levels)", "SprintLab", 899, 699, 55, "Latex loop bands from light to extra heavy.", True),
    ("cardio-conditioning", "Ab Roller with Knee Mat", "SprintLab", 799, None, 30, "Dual-wheel roller for stable core work.", False),
    ("cardio-conditioning", "Battle Rope 9 m", "SprintLab", 3299, 2799, 8, "Poly-dacron rope for high-intensity conditioning.", False),
    ("cardio-conditioning", "Agility Ladder 6 m", "SprintLab", 599, None, 3, "Flat rungs for footwork and speed drills.", False),
    ("yoga-recovery", "Non-slip Yoga Mat 6 mm", "FlowState", 1199, 899, 60, "Textured TPE surface with a carry strap.", True),
    ("yoga-recovery", "High-density Foam Roller", "FlowState", 999, 799, 35, "Eases tight quads, calves and back after training.", False),
    ("yoga-recovery", "Yoga Block Pair", "FlowState", 699, None, 45, "Firm EVA foam blocks for alignment and support.", False),
    ("cricket", "English Willow Bat (Size 6)", "StrikeZone", 6999, 5799, 7, "Grade-2 willow with a thick edge and mid-high sweet spot.", False),
    ("cricket", "Leather Cricket Ball (Pack of 3)", "StrikeZone", 1099, 899, 50, "Four-piece construction with hand-stitched seam.", False),
    ("cricket", "Batting Gloves", "StrikeZone", 1599, 1299, 20, "Padded fingers with a breathable palm.", False),
    ("badminton-racket-sports", "Graphite Badminton Racket", "CourtCraft", 2499, 1899, 22, "Lightweight head-heavy frame for powerful smashes.", True),
    ("badminton-racket-sports", "Feather Shuttlecocks (12)", "CourtCraft", 899, None, 70, "Goose feather shuttles with a cork base.", False),
    ("badminton-racket-sports", "Racket Kit Bag", "CourtCraft", 1299, 999, 26, "Thermal-lined compartments for up to 6 rackets.", False),
    ("footwear-apparel", "CushionRun Training Shoes", "StrideX", 3499, 2799, 30, "Responsive foam and a breathable mesh upper.", True),
    ("footwear-apparel", "Dry-fit Training T-shirt", "StrideX", 799, 599, 90, "Quick-dry fabric with flatlock seams.", False),
    ("footwear-apparel", "Stretch Training Shorts", "StrideX", 899, None, 65, "Four-way stretch with a zip pocket.", False),
    ("gym-accessories", "Lifting Gloves with Wrist Wrap", "GripWorks", 699, 549, 48, "Padded palms and a supportive wrist strap.", False),
    ("gym-accessories", "Leather Lifting Belt", "GripWorks", 2299, 1899, 14, "10 mm lever-free belt for heavy squats and deadlifts.", False),
    ("gym-accessories", "Steel Shaker Bottle 750 ml", "GripWorks", 599, 449, 85, "Leak-proof lid and a mixing ball.", False),
    ("gym-accessories", "Gym Duffel Bag", "GripWorks", 1499, 1199, 24, "Separate shoe compartment and water-resistant base.", False),
    ("gym-accessories", "Digital Weighing Scale", "GripWorks", 1199, 899, 0, "Tempered glass platform; tracks up to 180 kg.", False),
]

# (name, muscle, equipment level 0-2, difficulty 0-2, cue)
EXERCISES = [
    ("Push-up", "chest", 0, 0, "Hands under shoulders, body in a straight line, chest to just above the floor."),
    ("Incline push-up", "chest", 0, 0, "Hands on a bench or sturdy table to make the push-up easier."),
    ("Diamond push-up", "chest", 0, 1, "Hands close together under the chest; keep elbows tucked."),
    ("Dumbbell bench press", "chest", 1, 0, "Lower the dumbbells to chest level, press up without locking out hard."),
    ("Dumbbell fly", "chest", 1, 1, "Slight elbow bend, open wide, squeeze back together."),
    ("Machine chest press", "chest", 2, 0, "Set the seat so handles sit at mid-chest."),
    ("Barbell bench press", "chest", 2, 1, "Shoulder blades pinched, feet planted, bar to mid-chest."),
    ("Cable fly", "chest", 2, 1, "Step forward, soft elbows, bring hands together in an arc."),
    ("Superman hold", "back", 0, 0, "Lie face down, lift arms and legs, hold for two seconds."),
    ("Reverse snow angel", "back", 0, 0, "Face down, sweep arms from hips to overhead with control."),
    ("Resistance band row", "back", 1, 0, "Anchor the band, pull elbows back, squeeze shoulder blades."),
    ("One-arm dumbbell row", "back", 1, 0, "Hand and knee on a bench, pull the dumbbell to your hip."),
    ("Lat pulldown", "back", 2, 0, "Pull the bar to upper chest, elbows down and back."),
    ("Seated cable row", "back", 2, 0, "Sit tall, pull the handle to your belly, avoid swinging."),
    ("Barbell bent-over row", "back", 2, 1, "Hinge at the hips with a flat back, row to the lower ribs."),
    ("Pull-up", "back", 2, 2, "Full hang to chin over bar; use a band if you need help."),
    ("Bodyweight squat", "legs", 0, 0, "Feet shoulder-width, sit back and down, drive through the heels."),
    ("Glute bridge", "legs", 0, 0, "Lie on your back, press hips up, squeeze at the top."),
    ("Reverse lunge", "legs", 0, 0, "Step back, lower the back knee, push through the front heel."),
    ("Jump squat", "legs", 0, 1, "Squat down, jump explosively, land softly."),
    ("Goblet squat", "legs", 1, 0, "Hold one dumbbell at the chest and squat deep."),
    ("Dumbbell Romanian deadlift", "legs", 1, 1, "Soft knees, push hips back, feel the hamstrings stretch."),
    ("Leg press", "legs", 2, 0, "Feet shoulder-width, lower until knees reach about 90 degrees."),
    ("Leg curl machine", "legs", 2, 0, "Curl smoothly, pause, and lower with control."),
    ("Barbell back squat", "legs", 2, 1, "Bar on upper back, brace your core, squat to parallel or lower."),
    ("Conventional deadlift", "legs", 2, 2, "Bar over midfoot, flat back, push the floor away."),
    ("Plank shoulder taps", "shoulders", 0, 0, "From a plank, tap each shoulder without rocking your hips."),
    ("Wall angel", "shoulders", 0, 0, "Back to the wall, slide arms up and down keeping contact."),
    ("Pike push-up", "shoulders", 0, 1, "Hips high in an inverted V, lower the head toward the floor."),
    ("Band lateral raise", "shoulders", 1, 0, "Stand on the band, raise arms to shoulder height."),
    ("Dumbbell shoulder press", "shoulders", 1, 0, "Press overhead from shoulder height, ribs down."),
    ("Dumbbell lateral raise", "shoulders", 1, 0, "Lead with the elbows, stop at shoulder height."),
    ("Machine shoulder press", "shoulders", 2, 0, "Adjust the seat so handles start at ear level."),
    ("Barbell overhead press", "shoulders", 2, 1, "Squeeze glutes, press the bar in a straight line over the head."),
    ("Cable face pull", "shoulders", 2, 1, "Pull the rope to your face, elbows high, squeeze the rear delts."),
    ("Isometric towel curl", "arms", 0, 0, "Pull against a towel under your foot, holding tension."),
    ("Bench dip", "arms", 0, 0, "Hands on a bench edge, lower until elbows reach 90 degrees."),
    ("Close-grip push-up", "arms", 0, 1, "Hands under the chest, elbows brushing the ribs."),
    ("Dumbbell biceps curl", "arms", 1, 0, "Elbows pinned, curl up, lower slowly."),
    ("Hammer curl", "arms", 1, 0, "Palms facing in, curl without swinging."),
    ("Overhead triceps extension", "arms", 1, 0, "Lower the dumbbell behind the head, extend fully."),
    ("Cable triceps pushdown", "arms", 2, 0, "Elbows by your sides, press down and squeeze."),
    ("Barbell curl", "arms", 2, 1, "Strict curl, no body swing."),
    ("Plank", "core", 0, 0, "Forearms down, body straight, breathe steadily."),
    ("Dead bug", "core", 0, 0, "Lower opposite arm and leg slowly, back flat on the floor."),
    ("Bicycle crunch", "core", 0, 0, "Opposite elbow to knee, slow and controlled."),
    ("Lying leg raise", "core", 0, 1, "Keep your lower back pressed down as you lift and lower."),
    ("Russian twist", "core", 1, 0, "Lean back slightly and rotate through the torso."),
    ("Hanging knee raise", "core", 2, 1, "Hang from a bar, lift knees to hip height without swinging."),
    ("Cable crunch", "core", 2, 1, "Kneel, curl the ribs toward the pelvis."),
    ("Jumping jacks", "cardio", 0, 0, "Easy rhythm to raise your heart rate."),
    ("High knees", "cardio", 0, 0, "Drive knees to hip height, pump the arms."),
    ("Mountain climbers", "cardio", 0, 1, "From a plank, run the knees toward the chest."),
    ("Burpees", "cardio", 0, 1, "Squat, kick back, push-up, jump up. Scale as needed."),
    ("Skipping rope", "cardio", 1, 0, "Light bounces on the balls of the feet."),
    ("Treadmill brisk walk or jog", "cardio", 2, 0, "Build to a pace where you can still talk."),
    ("Stationary bike intervals", "cardio", 2, 0, "30 seconds hard, 60 seconds easy."),
    ("Rowing machine intervals", "cardio", 2, 1, "Legs, then body, then arms; reverse on the return."),
]


class Command(BaseCommand):
    help = "Load demo categories, products and the exercise library (safe to run more than once)."

    def handle(self, *args, **options):
        cats = {}
        for pos, (name, slug, desc) in enumerate(CATEGORIES):
            cats[slug], _ = Category.objects.update_or_create(slug=slug, defaults={"name": name, "description": desc, "position": pos})
        made = 0
        for slug, name, brand, mrp, sale, stock, short, featured in PRODUCTS:
            _, created = Product.objects.get_or_create(name=name, defaults={
                "category": cats[slug], "brand": brand, "price": Decimal(mrp),
                "discount_price": Decimal(sale) if sale else None, "stock": stock,
                "short_description": short, "description": short + "\n\nDemo product: edit or replace it from the admin panel.",
                "is_featured": featured,
            })
            made += created
        ex_made = 0
        for name, muscle, equip, diff, cue in EXERCISES:
            _, created = Exercise.objects.get_or_create(name=name, defaults={
                "muscle_group": muscle, "equipment_level": equip, "difficulty": diff, "description": cue})
            ex_made += created
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(CATEGORIES)} categories, {made} new products, {ex_made} new exercises."))
