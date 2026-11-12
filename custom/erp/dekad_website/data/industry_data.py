# -*- coding: utf-8 -*-
from .translate_utils import _lt

INDUSTRIES_CATALOG = {
    'education': {
        'hero_title': _lt('Empowering Education Through Smart Management'),
        'hero_desc': _lt('Streamline school operations, boost student engagement, and simplify administration — all with our unified education platform.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/education/hero_bg_image.png',

        'showcase_title': _lt('Built for Schools, Colleges & Training Centers'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/education/showcase_image.webp',
        'showcase_features': [
            {
                'icon': 'fa-arrows-alt',
                'title': _lt('Centralized Academic Management'),
                'desc': _lt('Unify student and staff records, class schedules, attendance, and assessments.')
            },
            {
                'icon': 'fa-group',
                'title': _lt('Parent & Student Portals'),
                'desc': _lt('Enable real-time communication and access to learning resources and updates.')
            },
            {
                'icon': 'fa-gears',
                'title': _lt('Automation That Saves Time'),
                'desc': _lt('From fee management to report card generation — let the system handle routine tasks.')
            }
        ],

        'cards_title': _lt('Features Tailored for the Education Sector'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image.png',
                'title': _lt('Student & Parents Profiles'),
                'desc': _lt('Maintain detailed records—including grades, roles, attendance, and documents.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image_2.png',
                'title': _lt('Timetable & Scheduling'),
                'desc': _lt('Create academic calendars, class routines, and teacher assignments using a flexible, drag‑and‑drop interface.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image_3.webp',
                'title': _lt('Assessments & Report Cards'),
                'desc': _lt('Set up exam structures, enter grades, and automatically generate performance reports and analytics.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image_4.webp',
                'title': _lt('Online Admissions & Registration'),
                'desc': _lt('Collect student data and required documents via digital application forms with approval workflows.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image_5.png',
                'title': _lt('Communication & Notifications'),
                'desc': _lt('Send alerts, newsletters, and updates to parents and students via email, SMS, or portal messaging.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/education/image_6.png',
                'title': _lt('Fee & Financial Management'),
                'desc': _lt('Track tuition payments, generate invoices, apply scholarships, and monitor outstanding balances.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/education/masonry_image.webp',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Integrated Learning Tools'),
                'desc': _lt('Share assignments, resources, and announcements through the portal.'),
                'grid_area': '1 / 6 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Real-Time Dashboards'),
                'desc': _lt('Monitor attendance trends, academic progress, and finances with intuitive KPI dashboards.'),
                'grid_area': '1 / 10 / 5 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 0px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('HR & Payroll Support'),
                'desc': _lt('Manage teacher contracts, time tracking, leaves, and performance evaluations centrally.'),
                'grid_area': '5 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 50px;'
            }
        ]
    },
    'manufacturing': {
        'hero_title': _lt('Smarter Manufacturing Starts Here'),
        'hero_desc': _lt('Plan, track, and optimize your production from raw materials to finished goods — all in one platform.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/manufacturing/hero_bg_image.png',

        'showcase_title': _lt('From small workshops to full-scale factories'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/manufacturing/showcase_image.svg',
        'showcase_features': [
            {
                'icon': 'fa-arrows-alt',
                'title': _lt('End-to-End Visibility'),
                'desc': _lt('Gain complete control over production, inventory, and supply chains.')
            },
            {
                'icon': 'fa-bar-chart-o',
                'title': _lt('Real-Time Tracking'),
                'desc': _lt('Monitor work orders, material movements, and timelines as they happen.')
            },
            {
                'icon': 'fa-gears',
                'title': _lt('Integrated Operations'),
                'desc': _lt('All departments — production, sales, purchasing, and finance — working from a unified system.')
            }
        ],

        'cards_title': _lt('Powerful Features for Manufacturing Teams'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image.png',
                'title': _lt('Production Management'),
                'desc': _lt('Create manufacturing orders, schedule production runs, and define routing processes for full efficiency.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image_2.png',
                'title': _lt('Inventory Control'),
                'desc': _lt('Track raw materials, semi-finished, and finished products using real-time stock levels and barcode scanning.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image_3.png',
                'title': _lt('Quality Assurance'),
                'desc': _lt('Define control points, launch quality checks, and manage non-conformance cases directly within the workflow.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image_4.png',
                'title': _lt('Work Center Scheduling'),
                'desc': _lt('Assign tasks, balance workloads, and view production calendars to avoid bottlenecks.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image_5.png',
                'title': _lt('Bill of Materials (BoM)'),
                'desc': _lt('Build flexible multi-level BoMs with variants and cost breakdowns — essential for custom or batch production.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/manufacturing/image_6.png',
                'title': _lt('Live Dashboards & Reports'),
                'desc': _lt('Analyze performance metrics like production lead time, material usage, and overall efficiency.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/manufacturing/masonry_image.webp',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Seamless Sales Link'),
                'desc': _lt('Convert confirmed sales into production orders with delivery timelines and inventory planning built-in.'),
                'grid_area': '1 / 6 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Integrated Purchasing'),
                'desc': _lt('Automate reorders for raw materials based on stock levels and production needs.'),
                'grid_area': '1 / 10 / 5 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 0px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Unified Costing & Accounting'),
                'desc': _lt('Automatically track material and labor costs for each order — linked directly to your financials.'),
                'grid_area': '5 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 50px;'
            }
        ]
    },
    'construction': {
        'hero_title': _lt('Construction Project Management Made Simple'),
        'hero_desc': _lt('Plan, budget, and execute construction projects with real-time tracking, centralized documentation, and team collaboration.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/construction/hero_bg_image.png',

        'showcase_title': _lt('Keep your projects on time, on budget, and under control'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/construction/showcase_image.svg',
        'showcase_features': [
            {
                'icon': 'fa-thumb-tack',
                'title': _lt('Centralized Project Oversight'),
                'desc': _lt('Monitor tasks, deadlines, and budgets in real-time — all in one platform.')
            },
            {
                'icon': 'fa-chain',
                'title': _lt('Field-to-Office Connectivity'),
                'desc': _lt('Connect site teams with engineers, managers, and finance from anywhere.')
            },
            {
                'icon': 'fa-calendar',
                'title': _lt('Smarter Resource Planning'),
                'desc': _lt('Track labor, materials, equipment, and subcontractors with complete transparency.')
            }
        ],

        'cards_title': _lt('Features Tailored for the Construction Industry'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image.webp',
                'title': _lt('Project Management'),
                'desc': _lt('Define phases, assign tasks, monitor Gantt charts, and keep everyone aligned on project timelines.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image_2.webp',
                'title': _lt('Document Control'),
                'desc': _lt('Organize blueprints, contracts, permits, and inspection reports with access control and versioning.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image_3.webp',
                'title': _lt('Timesheets & Attendance'),
                'desc': _lt('Track work hours, labor costs, and site attendance with mobile check-ins and approval workflows.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image_4.webp',
                'title': _lt('Budget & Cost Tracking'),
                'desc': _lt('Monitor estimated vs. actual costs in real-time — labor, materials, and overheads.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image_5.png',
                'title': _lt('Inventory & Materials'),
                'desc': _lt('Control material requests, delivery schedules, stock levels, and consumption on each site.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/construction/image_6.webp',
                'title': _lt('Progress Reports'),
                'desc': _lt('Generate site reports, safety logs, and KPIs with just a few clicks.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/construction/masonry_image.png',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Linked Procurement'),
                'desc': _lt('Convert material requests into purchase orders and track delivery directly to the site.'),
                'grid_area': '1 / 6 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Real-Time Invoicing'),
                'desc': _lt('Create and send invoices based on milestones, completed work, or contracts — instantly.'),
                'grid_area': '1 / 10 / 5 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 0px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Integrated HR & Payroll'),
                'desc': _lt('Manage workers, contracts, payslips, and site-specific assignments — all in one place.'),
                'grid_area': '5 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 50px;'
            }
        ]
    },
    'agriculture': {
        'hero_title': _lt('Grow Your Agro‑Business with Smart Management'),
        'hero_desc': _lt('Manage sales, procurement, inventory, customer relations, field services, and projects—from farm to storefront—in one intuitive system.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/agriculture/hero_bg_image.jpg',

        'showcase_title': _lt('Streamline your operations from planting season to point of sale.'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/agriculture/showcase_image.svg',
        'showcase_features': [
            {
                'icon': 'fa-tag',
                'title': _lt('Unified Sales Channels'),
                'desc': _lt('Seamlessly sell via eCommerce and in-store POS with custom pricelists, promotions, checkout options, and multiple payment methods.')
            },
            {
                'icon': 'fa-random',
                'title': _lt('Leads & CRM Tracking'),
                'desc': _lt('Capture inquiries from website forms, calls, or site visits and convert them into quotes or orders.')
            },
            {
                'icon': 'fa-file-text-o',
                'title': _lt('Quotation & Project Workflows'),
                'desc': _lt('Create professional quotes—complete with materials, labor, and services—and automate project creation upon approval.')
            },
            {
                'icon': 'fa-wrench',
                'title': _lt('Mobile & Field Service Scheduling'),
                'desc': _lt('Automatically assign tasks, schedule shifts, and log timesheets during site visits.')
            }
        ],

        'cards_title': _lt('Core Features for Agro‑Stores, Gardeners & Farming Projects'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image.webp',
                'title': _lt('Online & In‑Store Sales'),
                'desc': _lt('Configure your eCommerce store, POS terminals, promo codes, and one-click checkout—for both B2B and B2C.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_2.webp',
                'title': _lt('Automated Purchase & Restock'),
                'desc': _lt('Send RFQs to vendors, receive stock with validation checks, and trigger replenishment automatically.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_3.png',
                'title': _lt('Shipping & Fulfillment'),
                'desc': _lt('Integrate with major carriers (DHL, FedEx, UPS, USPS, etc.) for seamless delivery operations.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_4.png',
                'title': _lt('Invoicing & Loyalty Programs'),
                'desc': _lt('Generate invoices with QR codes and loyalty points to build long-term customer relationships.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_5.png',
                'title': _lt('Integrated Reporting'),
                'desc': _lt('Track sales trends, stock levels, promo success, and store performance with dashboards.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_6.webp',
                'title': _lt('CRM Pipeline'),
                'desc': _lt('Organize and track your leads through every stage of the sales cycle. Assign opportunities, schedule activities, and monitor progress to close deals faster—all in one streamlined view.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_7.webp',
                'title': _lt('Quote Builder & Calculator'),
                'desc': _lt('Use templates and dynamic pricing or connect spreadsheets for quote accuracy .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_8.png',
                'title': _lt('Valid Electronic Signatures'),
                'desc': _lt('Sign contracts and quotes compliantly across regions .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_9.png',
                'title': _lt('Document & CAD Attachments'),
                'desc': _lt('Attach plans, blueprints, CAD/3D files to quotes and projects.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_10.webp',
                'title': _lt('Project & Task Management'),
                'desc': _lt('Automate project creation, track tasks, subtasks, stages, tags, and activities.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_11.webp',
                'title': _lt('Integrated Timesheets'),
                'desc': _lt('Record onsite labor hours directly against tasks.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_12.webp',
                'title': _lt('Task Scheduling & Planning'),
                'desc': _lt('Balance schedules, shifts, and field visits.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_13.webp',
                'title': _lt('Inventory Management'),
                'desc': _lt('Manage stock, automate replenishment, track delivery orders.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_14.webp',
                'title': _lt('Financial & Invoicing Tools'),
                'desc': _lt('Handle invoicing, down payments, milestone billing, QR-code invoices.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_15.webp',
                'title': _lt('Shopping Channels'),
                'desc': _lt('POS, eCommerce storefronts, and offline stores .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/agriculture/image_16.png',
                'title': _lt('Analytical Reporting'),
                'desc': _lt('Track project profitability, sales trends, stock levels, and efficiency KPIs.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/agriculture/masonry_image.webp',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Sale-to-Project Automation'),
                'desc': _lt('Confirm a quote and automatically launch a project with tasks and resource assignments.'),
                'grid_area': '1 / 6 / 6 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Live Inventory Updates'),
                'desc': _lt('Stock movements from online orders, POS sales, or deliveries update instantly.'),
                'grid_area': '1 / 10 / 6 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 0px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Unified Work & Financial Tracking'),
                'desc': _lt('Track labor, materials, project costs, and generate invoices—all linked together.'),
                'grid_area': '6 / 6 / 10 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 50px;'
            }
        ]
    },
    'hospitality': {
        'hero_title': _lt('Hospitality Management, Simplified'),
        'hero_desc': _lt('Oversee bookings, guest services, and on-site operations with a unified, real-time platform.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/hospitality/hero_bg_image.jpg',

        'showcase_title': _lt('Built for Hotels, Restaurants & Resorts'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/hospitality/showcase_image.png',
        'showcase_features': [
            {
                'icon': 'fa-puzzle-piece',
                'title': _lt('Integrated Room Reservation'),
                'desc': _lt('Handle room bookings with instant availability and confirmation across channels.')
            },
            {
                'icon': 'fa-spoon',
                'title': _lt('Comprehensive Food & Beverage Management'),
                'desc': _lt('Manage restaurant orders, minibar services, and event catering—all in one system')
            },
            {
                'icon': 'fa-wrench',
                'title': _lt('Efficient Housekeeping & Maintenance'),
                'desc': _lt('Schedule cleanings, track room status, and log maintenance with automation')
            },
            {
                'icon': 'fa-group',
                'title': _lt('Transport & Event Services'),
                'desc': _lt('Coordinate guest transportation and on-site events from the same platform.')
            }
        ],

        'cards_title': _lt('Key Features for Hospitality Operations'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image.png',
                'title': _lt('Room Reservation'),
                'desc': _lt('Reserve Hotel Rooms based on requirement of Room Capacity and Room Type')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_2.png',
                'title': _lt('Room Status Tracking'),
                'desc': _lt('Monitor which rooms are available, reserved, or under maintenance in real-time.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_3.png',
                'title': _lt('Customer & Guest Profiles'),
                'desc': _lt('Keep detailed records of guest data, preferences, and visit history to enhance personalized service.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_4.png',
                'title': _lt('Multi-Company / Branch Support'),
                'desc': _lt('Manage multiple hotel branches from a single backend system.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_5.png',
                'title': _lt('Real-Time Reporting'),
                'desc': _lt('View occupancy levels, revenue, service usage, and housekeeping performance.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_6.webp',
                'title': _lt('Staff & User Roles'),
                'desc': _lt('Assign user rights for front desk, housekeeping, managers, and F&B staff.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_7.png',
                'title': _lt('Digitize accounting and financials'),
                'desc': _lt('Track income, expenses, assets, and liabilities in real-time.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_8.png',
                'title': _lt('Monitor restaurant and POS transactions'),
                'desc': _lt('Track dine-in, room service, and counter orders from a single screen.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_9.png',
                'title': _lt('Manage cleaning schedules'),
                'desc': _lt('Assign rooms, set priorities, and monitor cleaning performance.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/hospitality/image_10.png',
                'title': _lt('Handle maintenance'),
                'desc': _lt('Log issues, assign to teams, and track progress until resolution.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/hospitality/masonry_image.jpg',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Cross-Module Integration'),
                'desc': _lt('Orders in restaurants or mini-bar automatically update room charges; inventory and accounting update instantly.'),
                'grid_area': '1 / 6 / 6 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Operational Insights'),
                'desc': _lt('Dashboards reveal occupancy trends, staffing needs, maintenance backlogs, and F&B revenue performance.'),
                'grid_area': '1 / 10 / 6 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 0px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Booking → Stay → Billing'),
                'desc': _lt('Reservations flow directly into check-in, service consumption, and final invoicing.'),
                'grid_area': '6 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-x: 20px; --grid-item-padding-y: 30px;'
            }
        ]
    },
    'audit-certification': {
        'hero_title': _lt('Audit & Certification Management'),
        'hero_desc': _lt('Control documents, approvals, and compliance — all from a single, smart platform.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/audit-certification/hero_bg_image.jpg',

        'showcase_title': _lt('Smart tools to reduce paperwork and human error.'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/audit-certification/showcase_image.svg',
        'showcase_features': [
            {
                'icon': 'fa-refresh',
                'title': _lt('Automate Compliance'),
                'desc': _lt('Set up approval flows, validation rules, and reminders to ensure every step is audit-ready.')
            },
            {
                'icon': 'fa-unlink',
                'title': _lt('Track Certifications'),
                'desc': _lt('Monitor expiration dates, renewals, and staff training progress with automatic alerts.')
            },
            {
                'icon': 'fa-external-link-square',
                'title': _lt('Improve Transparency'),
                'desc': _lt('Maintain a centralized database of records, actions, and audit logs for easy reporting.')
            }
        ],

        'cards_title': _lt('Features Tailored for Audit & Certification Teams'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/audit-certification/image.png',
                'title': _lt('Document Management'),
                'desc': _lt('Upload, organize, and share compliance documents with access controls and versioning.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/audit-certification/image_2.png',
                'title': _lt('Audit Scheduling'),
                'desc': _lt('Plan and assign internal or external audits. Track progress, deadlines, and findings in one view.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/audit-certification/image_3.png',
                'title': _lt('Certification & Training'),
                'desc': _lt('Assign training programs to staff and manage certificates with renewal dates and alerts.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/audit-certification/image_4.png',
                'title': _lt('Dashboard & Reporting'),
                'desc': _lt('Real-time insights into compliance status, pending actions, and upcoming deadlines.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/audit-certification/masonry_image.png',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Linked Employee Certifications'),
                'desc': _lt('Link certifications with employee profiles'),
                'grid_area': '1 / 6 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('One-Click Audit Reporting'),
                'desc': _lt('Generate audit-ready reports in one click'),
                'grid_area': '1 / 10 / 5 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Unified Team Coordination'),
                'desc': _lt('Seamless coordination between compliance, HR, and project teams'),
                'grid_area': '5 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            }
        ]
    },
    'retail': {
        'hero_title': _lt('Retail Management Made Easy'),
        'hero_desc': _lt('Sync sales, inventory, and customer experiences — across all your physical and digital channels.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/retail/hero_bg_image.jpg',

        'showcase_title': _lt('Designed for physical stores, online shops, and hybrid retail brands.'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/retail/showcase_image.png',
        'showcase_features': [
            {
                'icon': 'fa-check-square-o',
                'title': _lt('All-in-One Sales Platforms'),
                'desc': _lt('Manage in-store POS, online eCommerce, B2B sales, and mobile kiosks in one system.')
            },
            {
                'icon': 'fa-refresh',
                'title': _lt('Always-Accurate Inventory'),
                'desc': _lt('Barcode & scale support, real-time stock sync, lot/serial tracking, expiration dates, and automated replenishment .')
            },
            {
                'icon': 'fa-tag',
                'title': _lt('Loyalty, Coupons & Promotions'),
                'desc': _lt('Build customer loyalty with cards, points, bulk discounts, coupons, e-wallets, and gift cards.')
            },
            {
                'icon': 'fa-money',
                'title': _lt('Multi-Payment & Multi-Cashier Support'),
                'desc': _lt('Accept cash, credit, digital wallets; manage badge/PIN-secured cashiers and shift plans.')
            },
            {
                'icon': 'fa-spinner',
                'title': _lt('Offline & Online Resilience'),
                'desc': _lt('POS stays fully functional when offline, syncing automatically later.')
            }
        ],

        'cards_title': _lt('Key Features for Retail Stores'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image.webp',
                'title': _lt('Point of Sale (POS)'),
                'desc': _lt('Quick, intuitive interface with barcode scanning, multiple payment methods, loyalty integration, and kiosk support.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_2.webp',
                'title': _lt('E‑Commerce & Click‑and‑Collect'),
                'desc': _lt('Launch a branded online store, support click‑&‑collect, cart abandonment recovery, built-in shipping options, and seamless stock sync .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_3.webp',
                'title': _lt('Purchasing & Suppliers'),
                'desc': _lt('Manage RFQs, supplier performance, landed costs, and systematic vendor follow-ups for efficient restocking.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_4.png',
                'title': _lt('Shipping Integration'),
                'desc': _lt('Connect with DHL, FedEx, UPS, and others to automate label printing and cost calculation.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_5.png',
                'title': _lt('CRM & Marketing Automation'),
                'desc': _lt('Capture customer data, segment customers, and run email/SMS campaigns tied to behavior and loyalty activity .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_6.png',
                'title': _lt('Sales Analysis & Reports'),
                'desc': _lt('Monitor KPIs, best-selling products, peak hours, stockouts, and multi-store metrics in real time .')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_6.png',
                'title': _lt('Expiry Date Management'),
                'desc': _lt('Monitor expiration dates, get alerts for soon-to-expire items, and rotate stock efficiently. (Ideal for groceries, pharmaceuticals, and perishable goods)')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_7.webp',
                'title': _lt('Accounting & Integrated Payments'),
                'desc': _lt('Real-time accounting sync, multi-currency invoicing, seamless reconciliation, and flexible invoicing like QR-code payments')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_8.png',
                'title': _lt('Barcode Management'),
                'desc': _lt('Scan products instantly to update sales, inventory, batches, and expiry dates — for faster checkouts and error-free tracking.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/retail/image_9.webp',
                'title': _lt('Inventory Intelligence'),
                'desc': _lt('Track stock movements, set minimum/maximum levels, receive alerts on lots expiring soon, and auto-trigger purchase orders.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/retail/masonry_image.webp',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Complete Channel Integration'),
                'desc': _lt('Sync inventory, orders, and customer data in real time across POS, eCommerce, and mobile.'),
                'grid_area': '1 / 5 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Automated Back-Office'),
                'desc': _lt('Sales → stock moves → invoicing → accounting flows automatically, saving time and errors.'),
                'grid_area': '1 / 10 / 9 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-y: 70px; --grid-item-padding-x: 20px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Customer-Driven Growth'),
                'desc': _lt('Loyalty rewards, promotions, and CRM tied into sales and marketing performance—every transaction informs the next campaign.'),
                'grid_area': '5 / 5 / 9 / 10',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-y: 50px; --grid-item-padding-x: 20px;'
            }
        ]
    },
    'law-firm': {
        'hero_title': _lt('Legal Practice Management, Simplified'),
        'hero_desc': _lt('Manage your firm from client intake to case resolution—securely, efficiently, and all-in-one.'),
        'hero_bg_image': '/dekad_website/static/src/img/migrated/industries/law-firm/hero_bg_image.jpg',

        'showcase_title': _lt('Ideal for law firms, consultants, and corporate legal teams.'),
        'showcase_image': '/dekad_website/static/src/img/migrated/industries/law-firm/showcase_image.png',
        'showcase_features': [
            {
                'icon': 'fa-check-square-o',
                'title': _lt('Online Appointment Booking'),
                'desc': _lt('Showcase appointment types on your website and let clients book directly—synchronized with your calendar.')
            },
            {
                'icon': 'fa-group',
                'title': _lt('CRM-Powered Client Intake'),
                'desc': _lt('Use structured CRM pipelines to assess leads and move them seamlessly into a legal workflow.')
            },
            {
                'icon': 'fa-book',
                'title': _lt('Proposal & Contract Management'),
                'desc': _lt('Handle quotations, engagement letters, and service agreements with signed documentation.')
            }
        ],

        'cards_title': _lt('Key Features for Law Firms'),
        'cards': [
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image.png',
                'title': _lt('Calendar & Scheduling'),
                'desc': _lt('Manage consultations, court dates, and internal meetings visually and intuitively.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_2.png',
                'title': _lt('Centralized Case Management'),
                'desc': _lt('Create a project for every case—with tasks, tags, deadlines, and follow-ups in one dashboard.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_3.png',
                'title': _lt('Secure eSigning'),
                'desc': _lt('Send and sign legal documents—contracts, letters, engagement forms—with validated digital signatures.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_4.webp',
                'title': _lt('Timesheets & Billing'),
                'desc': _lt('Record billable time per case and integrate automatically with invoicing—whether hourly, milestone, or flat rate.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_5.png',
                'title': _lt('Flexible Invoicing'),
                'desc': _lt('Generate invoices from timesheets, fixed assignments, or milestone achievements—complete with reminders and payment tracking.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_6.webp',
                'title': _lt('Document Workspace'),
                'desc': _lt('Store and manage contracts, filings, correspondence, and evidence—all linked to cases with version control.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_7.png',
                'title': _lt('Professional Website'),
                'desc': _lt('Create a branded site to present services, team credentials, FAQs, and client testimonials, with pre-built templates and AI enhancements.')
            },
            {
                'image': '/dekad_website/static/src/img/migrated/industries/law-firm/image_8.png',
                'title': _lt('Project & Case Dashboard'),
                'desc': _lt('Get a clear overview of case progress, time spent, costs, and next actions—all in one view.')
            }
        ],

        'masonry_image': '/dekad_website/static/src/img/migrated/industries/law-firm/masonry_image.png',
        'masonry_overlay_text': _lt('Everything Connected'),
        'masonry_blocks': [
            {
                'title': _lt('Smart Legal Workflow'),
                'desc': _lt('From client intake to final invoice — all steps flow seamlessly.'),
                'grid_area': '1 / 6 / 5 / 10',
                'bg_class': 'o_cc o_cc2',
                'bg_style': '--grid-item-padding-y: 20px; --grid-item-padding-x: 20px;'
            },
            {
                'title': _lt('Real-Time Dashboards'),
                'desc': _lt('Monitor billable hours, deadlines, and team workload at a glance.'),
                'grid_area': '1 / 10 / 5 / 13',
                'bg_class': 'o_cc o_cc3',
                'bg_style': '--grid-item-padding-y: 0px; --grid-item-padding-x: 20px; background-image: linear-gradient(135deg, rgb(255, 255, 255) -400%, rgb(21, 31, 49) 100%);'
            },
            {
                'title': _lt('Linked Documents & Time'),
                'desc': _lt('Track case files, timesheets, and signed contracts in one place.'),
                'grid_area': '5 / 6 / 9 / 13',
                'bg_class': 'o_cc o_cc4',
                'bg_style': '--grid-item-padding-y: 50px; --grid-item-padding-x: 20px;'
            }
        ]
    }
}