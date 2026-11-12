# -*- coding: utf-8 -*-
from .translate_utils import _lt

APPS_CATALOG = {
    'accounting-finance': {
        'slug': 'accounting-finance',
        'name': _lt('Accounting & Invoicing'),
        'subtitle': _lt('One smart platform to run your entire finance function—from invoicing and reconciliation to tax and reporting.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/accounting-finance/cover_bg.png',
        'overview': {
            'title': _lt('Flexible, Powerful & Future-Ready Finance for Growing Businesses'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we equip your finance team with the tools they need to work smarter—not harder. Our intelligent, cloud-based accounting platform goes beyond traditional bookkeeping to unify invoicing, bank reconciliation, tax management, digital signatures, document tracking, and real-time reporting in a single, connected ecosystem."),
                _lt("Designed for speed, accuracy, and scalability, our modular system adapts to your business as it grows—whether you're managing a single company or multiple entities across borders. With automated workflows and intuitive dashboards, you'll gain full control and visibility over your finances, reduce manual effort, and make faster, data-driven decisions.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Analytic Accounting'),
                'description': _lt('Track financial performance across departments, projects, or cost centers with multi-dimensional reporting.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_2.png'
            },
            {
                'title': _lt('Smart Bank Reconciliation'),
                'description': _lt('Connect to over 28,000 banks worldwide and match transactions in seconds with 95% accuracy.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_3.png'
            },
            {
                'title': _lt('Powerful Financial Dashboards'),
                'description': _lt('Get instant access to performance metrics, cash flow insights, and real-time P&L statements.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_4.webp'
            },
            {
                'title': _lt('Expense & Revenue Recognition'),
                'description': _lt('Easily manage deferrals and automate revenue/expense recognition over time with precision.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_5.png'
            },
            {
                'title': _lt('Real-Time Invoicing & Payments'),
                'description': _lt('Create, send, and track invoices with built-in automation and online payment options.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_6.png'
            },
            {
                'title': _lt('Multi-Company & Multi-Currency Support'),
                'description': _lt('Seamlessly create invoices across entities and currencies—complete with live exchange rates.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_7.webp'
            },
            {
                'title': _lt('Asset Management'),
                'description': _lt('Track assets, automate depreciation entries, and manage asset lifecycles seamlessly.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_8.png'
            },
            {
                'title': _lt('Advanced Tax & VAT Handling'),
                'description': _lt('Handle global transactions with automatic currency conversion and international tax compliance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_9.png'
            },
            {
                'title': _lt('Fully Integrated with All Odoo Modules'),
                'description': _lt('Seamlessly sync with Sales, Inventory, CRM, HR, and more for end-to-end operational visibility.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_10.webp'
            },
            {
                'title': _lt('Customizable Chart of Accounts'),
                'description': _lt('Tailor your financial structure for any industry, region, or business model.'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_11.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-shield',
                    'title': _lt('Multi-Company & Multi-Currency Ready'),
                    'description': _lt('Manage multiple companies, warehouses, and currencies—all in one place.')
                },
                {
                    'icon': 'fa-gear',
                    'title': _lt('Automation-First'),
                    'description': _lt('Eliminate repetitive tasks like invoice creation, bank matching, and tax filing with smart automation.')
                },
                {
                    'icon': 'fa-wrench',
                    'title': _lt('Tailored to Your Industry'),
                    'description': _lt('From retail to manufacturing, we adapt your finance tools to your specific business operations.')
                },
                {
                    'icon': 'fa-refresh',
                    'title': _lt('End-to-End Support from Dekad'),
                    'description': _lt('We don’t just install software—we partner with you for implementation, training, and ongoing optimization.')
                }
            ]
        }
    },
    'spreadsheet-ib': {
        'slug': 'spreadsheet-ib',
        'name': _lt('Spreadsheet (IB)'),
        'subtitle': _lt('Real‑time spreadsheets connected directly to your business data'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/accounting-finance/cover_bg.png',
        'overview': {
            'title': _lt('Collaborative, dynamic & intuitive – all within your ERP'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we empower you to analyze and act on live business data without juggling tools. Our integrated spreadsheet app pulls real-time information from Sales, Accounting, Inventory, CRM, and more—so you can build reports, dashboards, and forecasts with ease, all in one secure environment."),
                _lt("Designed for both power users and everyday teams, our spreadsheet solution brings data clarity and decision-making speed—no imports, no exports, no maintenance overhead.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/spreadsheet-ib/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Live Data Integration'),
                'description': _lt('Link reports directly to your Odoo database—pivot tables and charts stay updated automatically'),
                'image': '/dekad_website/static/src/img/migrated/apps/spreadsheet-ib/image_2.png'
            },
            {
                'title': _lt('Dynamic Pivot Tables'),
                'description': _lt('Create drag‑and‑drop pivot tables that reflect up-to-the-minute data from your ERP'),
                'image': '/dekad_website/static/src/img/migrated/apps/spreadsheet-ib/image_3.png'
            },
            {
                'title': _lt('Visual Charts & Dashboards'),
                'description': _lt('Transform data into bar, line, pie, waterfall, and combo charts on your spreadsheet dashboards'),
                'image': '/dekad_website/static/src/img/migrated/apps/accounting-finance/image_4.webp'
            },
            {
                'title': _lt('Conditional Formatting & Smart Filters'),
                'description': _lt('Highlight key trends with rules and easily find insights using advanced filters'),
                'image': '/dekad_website/static/src/img/migrated/apps/spreadsheet-ib/image_4.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-magic',
                    'title': _lt('Immediate Insights'),
                    'description': _lt('Stop waiting on IT or exports. Build reports, pivot, add charts, and share insights in minutes.')
                },
                {
                    'icon': 'fa-check',
                    'title': _lt('Faster Decision-Making'),
                    'description': _lt('Get ahead with dashboards that update automatically—see trends as they happen.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable and Secure'),
                    'description': _lt('From your first company to multi-entity groups, our spreadsheets scale safely with your business.')
                },
                {
                    'icon': 'fa-desktop',
                    'title': _lt('Familiar Interface'),
                    'description': _lt('Works like the spreadsheets you know—no training required—but with smarter connectivity.')
                }
            ]
        }
    },
    'cheque-management': {
        'slug': 'cheque-management',
        'name': _lt('Cheque Management'),
        'subtitle': _lt('Track, Manage, and Reconcile Cheques with Total Control'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/cheque-management/cover_bg.webp',
        'overview': {
            'title': _lt('Secure, Compliant, and Fully Integrated Cheque Lifecycle Management'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we make cheque handling seamless and stress-free. Our Cheque Management module gives you full visibility over incoming and outgoing cheques — from issuance and reception to clearance, return, or cancellation. With smart automation and integration across your Odoo Accounting and Payments modules, you’ll reduce errors, speed up reconciliation, and maintain strong audit trails."),
                _lt("Whether you're dealing with post-dated cheques, multi-currency payments, or cross-company operations, our solution ensures accuracy, security, and peace of mind throughout every transaction.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Receive or Send Money via Cheque'),
                'description': _lt('Easily manage incoming and outgoing PDC payments.'),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_2.png'
            },
            {
                'title': _lt('Integrated with Accounting'),
                'description': _lt('Synchronizes automatically with Odoo’s journal entries and general ledger, keeping your books up to date.'),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_3.png'
            },
            {
                'title': _lt('Detailed Cheque Information'),
                'description': _lt('Upload scanned copies or supporting documents (e.g., cheque images or bank slips) directly into the record.'),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_4.png'
            },
            {
                'title': _lt('Invoice/Bill Linking'),
                'description': _lt('Easily associate cheques with multiple invoices or bills for accurate reconciliation and tracking.'),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_5.png'
            },
            {
                'title': _lt('Multi-Stage Cheque Lifecycle'),
                'description': _lt('Follow cheques through clear stages: Draft, Registered, Bounced, Done, etc.'),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_6.png'
            },
            {
                'title': _lt('Document Attachments'),
                'description': _lt("Each cheque's PDC Status is clearly marked and updated through the interface, ensuring accounting transparency."),
                'image': '/dekad_website/static/src/img/migrated/apps/cheque-management/image_7.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-tasks',
                    'title': _lt('Tailored for UAE & GCC Markets'),
                    'description': _lt('Built with local banking norms and cheque workflows in mind — including post-dated and bounced cheque handling.')
                },
                {
                    'icon': 'fa-check',
                    'title': _lt('Multi-Company Ready'),
                    'description': _lt('Track cheque activity across multiple companies and bank accounts with full control.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Real-Time Visibility'),
                    'description': _lt('Gain full transparency across your financial operations — with dashboards and audit logs that update instantly.')
                },
                {
                    'icon': 'fa-exclamation',
                    'title': _lt('Minimize Risk & Manual Errors'),
                    'description': _lt('Avoid missed deadlines, duplicate entries, and unbalanced ledgers with automation.')
                }
            ]
        }
    },
    'sign': {
        'slug': 'sign',
        'name': _lt('E-Signatures'),
        'subtitle': _lt('Send, sign, and approve documents digitally from any device. Keep full audit trails, authentication, and regulatory compliance within a single unified platform.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/sign/cover_bg.webp',
        'overview': {
            'title': _lt('Secure, legal, and seamless e-signatures—anytime, anywhere'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we simplify how you handle contracts, approvals, and employee documents with Odoo Sign. Built-in workflows and cryptographic logging replace manual processes with speed, security, and professionalism.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/sign/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Custom Signature Input'),
                'description': _lt('Allow users to sign via handwritten fonts, drawing, or uploading a scanned signature.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_2.webp'
            },
            {
                'title': _lt('Drag & Drop Templates'),
                'description': _lt('Build reusable documents by placing fields, mandatory or optional, into PDFs—automating repetitive signatures.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_3.webp'
            },
            {
                'title': _lt('Signing Order & Multi-Role Support'),
                'description': _lt('Set the sequence of signers and assign distinct roles—ensuring controlled, role-based workflows.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_4.jpg'
            },
            {
                'title': _lt('Secure Authentication & Traceability'),
                'description': _lt('Authenticate signers via SMS or itsme®, capture IP address/time stamps, and embed cryptographic traces in audit logs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_5.jpg'
            },
            {
                'title': _lt('Automated Reminders & Delivery Control'),
                'description': _lt('Schedule automatic reminders, track progress, and send completed documents or CCs to designated recipients.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_6.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Complete ERP Integration'),
                    'description': _lt('Signature workflows embed directly within Sales, HR, Accounting, Recruitment, Rental, and Field Service modules—no extra apps needed.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Error-Free, Traceable Process'),
                    'description': _lt('Role-based fields, digital logs, and secure validation ensure each document is accurate, auditable, and legally binding.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Instant, Automated Workflow'),
                    'description': _lt('With reusable templates, reminders, and CC settings, you’ll reduce turnaround time and eliminate manual follow-up.')
                },
                {
                    'icon': 'fa-lightbulb-o',
                    'title': _lt('Universal Device Support'),
                    'description': _lt('Clients, employees, and partners can sign from any browser or mobile device—anywhere, any time.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Proven Security Framework'),
                    'description': _lt('Encrypted storage, SMS authentication, IP logging, and cryptographic seals keep your documents secure and trusted.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Implementation & Support'),
                    'description': _lt('Dekad sets up your templates, authorization flows, security options, and trains your team for confident, compliant adoption.')
                }
            ]
        }
    },
    'crm': {
        'slug': 'crm',
        'name': _lt('CRM'),
        'subtitle': _lt('Smarter Sales Management — From Lead Capture to Deal Closure'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/crm/cover_bg.png',
        'overview': {
            'title': _lt('Modern CRM with real-time insights — built to help you close more deals.'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our CRM empowers sales teams to work smarter and faster. Capture leads automatically (from email, website forms, live chat, VoIP, and events), nurture them effectively, and convert them into opportunities. With drag-and-drop pipelines, intelligent reminders, and mobile access, your team stays aligned and proactive—no matter where they are.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/crm/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation'
        },
        'key_features': [
            {
                'title': _lt('Smart Lead Capture'),
                'description': _lt('Automatically import leads from emails, web forms, chat, events—and enrich them with location and predictive scoring'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_2.png'
            },
            {
                'title': _lt('Visual Sales Pipeline'),
                'description': _lt('Drag-and-drop opportunities, customize stages by sales team, and analyze loss reasons to refine your process'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_3.png'
            },
            {
                'title': _lt('Activity-Driven Sales'),
                'description': _lt('Plan calls, meetings, and next steps today—automatically queue your activities and never miss a beat'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_4.webp'
            },
            {
                'title': _lt('Seamless Communication'),
                'description': _lt('Send templated emails, host live chats, and call through VoIP—all tracked in one place'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_5.png'
            },
            {
                'title': _lt('Accurate Forecasting & Dashboards'),
                'description': _lt('Monitor your KPIs in real time—forecast revenue, view cohorts, lead sources, and sales performance metrics'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_6.png'
            },
            {
                'title': _lt('Mobile CRM Access'),
                'description': _lt('Access your pipeline, schedule meetings, and log activities on the go with a mobile-optimized interface'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_7.png'
            },
            {
                'title': _lt('Predictive Lead Scoring & Deduplication'),
                'description': _lt('Prioritize the best leads and reduce duplicates with automated scoring and contact merging suggestions'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_8.png'
            },
            {
                'title': _lt('Contextual Customer Insights'),
                'description': _lt('See full history—webpages visited, emails, quotes, calls, and invoices—all in one unified, 360° view'),
                'image': '/dekad_website/static/src/img/migrated/apps/crm/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Unified ERP Ecosystem'),
                    'description': _lt("Our CRM doesn’t stand alone—it’s part of Odoo’s all-in-one system, connecting seamlessly with Sales, Inventory, Accounting, and more.")
                },
                {
                    'icon': 'fa-refresh',
                    'title': _lt('Sales-Driven Intelligence'),
                    'description': _lt('Track performance through real-time dashboards. Use insights and automation to prioritize leads and close faster.')
                },
                {
                    'icon': 'fa-sliders',
                    'title': _lt('Fully Customizable'),
                    'description': _lt('Customize pipelines, lead scoring, email templates, and activities to match your sales process and goals.')
                },
                {
                    'icon': 'fa-arrows',
                    'title': _lt('Scalable for Growth'),
                    'description': _lt('From freelancer to enterprise, we implement CRM solutions that grow with your business—multi-entity, multi-team, multi-currency ready.')
                }
            ]
        }
    },
    'sales': {
        'slug': 'sales',
        'name': _lt('Sales'),
        'subtitle': _lt('Sell Smarter — From Quote to Order to Invoice'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/sales/cover_bg.webp',
        'overview': {
            'title': _lt('Modern sales operations powered by automation and real-time insights'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Sales module streamlines your entire sales cycle. Generate dynamic, branded quotes instantly. Let customers self-serve through a rich portal experience with e-signatures and online payment. Customize pricing, manage products, and automate order workflows—all within a unified platform. Get better conversion rates, faster order processing, and total visibility from lead to revenue.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/sales/image.jpg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Instant Quotation Builder'),
                'description': _lt('Create polished quotes using templates, price lists, and signature-ready PDF output'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_2.png'
            },
            {
                'title': _lt('Customer Portal & e-Signature'),
                'description': _lt('Enable customers to review, sign, pay, and confirm orders online—no back‑and‑forth required .'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_3.webp'
            },
            {
                'title': _lt('Flexible Invoicing Options'),
                'description': _lt('Support down payments, pro-formas, milestone-based billing, and invoicing tied to delivery or time & materials'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_4.png'
            },
            {
                'title': _lt('Product & Price Control'),
                'description': _lt('Handle variants, pricelists, coupons, gift cards, loyalty programs, and margin-based shipping costs'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_5.png'
            },
            {
                'title': _lt('Upselling & Recommendations'),
                'description': _lt('Suggest optional or complementary products on quotes to increase average order value'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_6.png'
            },
            {
                'title': _lt('Automated Sales Workflows'),
                'description': _lt('Set activity reminders, alerts for key events, and inter-company order mirroring for multi-entity setups'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_7.png'
            },
            {
                'title': _lt('Insightful Reporting & Forecasting'),
                'description': _lt('Track revenue, pipeline health, churn, salesperson performance, MRR, and more with built-in analytics'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_8.png'
            },
            {
                'title': _lt('ERP-Wide Integration'),
                'description': _lt('Convert sales into invoices, delivery orders, and inventory flows; integrate seamlessly into CRM, POS, eCommerce, and accounting'),
                'image': '/dekad_website/static/src/img/migrated/apps/sales/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-flash',
                    'title': _lt('Fast Implementation & Training'),
                    'description': _lt('We adapt the system to your sales process, train your team, and ensure rapid adoption.')
                },
                {
                    'icon': 'fa-gear',
                    'title': _lt('Automated for Increased Productivity'),
                    'description': _lt('Automate pricing, quotes, follow-ups, upsells, and cross-company orders to reduce manual work.')
                },
                {
                    'icon': 'fa-wrench',
                    'title': _lt('Scalable for Growth'),
                    'description': _lt('Perfect for single or multi-company setups—with multi-currency, country-specific taxes, and inter-company flows.')
                },
                {
                    'icon': 'fa-check-square',
                    'title': _lt('Advanced Insights for Smarter Decisions'),
                    'description': _lt('No guesswork—your team gets real-time sales dashboards, forecasts, and performance metrics.')
                }
            ]
        }
    },
    'point-of-sale': {
        'slug': 'point-of-sale',
        'name': _lt('Point of Sale'),
        'subtitle': _lt('Sell anywhere—fast, digital, and fully in sync'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/point-of-sale/cover_bg.webp',
        'overview': {
            'title': _lt('User-friendly POS that works online or offline, on any device'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our POS system is built for speed, simplicity, and adaptability. Whether you’re on iPad, tablet, or desktop, you can start selling right away—even offline. With integrated payments, loyalty options, and scalable capabilities, our POS fits small shops to multi-store businesses flawlessly—while syncing in real-time with inventory, accounting, and customer data.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Multi-Device Ready & Offline Mode'),
                'description': _lt('Works on tablets, desktops, and industrial touch terminals—even without internet—syncing data when online'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_2.jpg'
            },
            {
                'title': _lt('Flexible Checkout & Payments'),
                'description': _lt('Support for cash, card terminals, checks, QR codes, split payments, tipping, and automated currency rounding'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_3.webp'
            },
            {
                'title': _lt('Efficient Order Management'),
                'description': _lt('Handle parallel orders, weight-based pricing, multi-step checkout, and order history searches quickly and intuitively'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_4.webp'
            },
            {
                'title': _lt('Smart Store Controls'),
                'description': _lt('Track cashier sessions, daily cash flow, and stock movements—all secured with PINs or badges'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_5.png'
            },
            {
                'title': _lt('Loyalty, Coupons & eWallet'),
                'description': _lt('Drive repeat business with loyalty points, gift cards, coupons, and digital credits across stores'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_6.png'
            },
            {
                'title': _lt('Dynamic Catalog & Barcode Support'),
                'description': _lt('Manage product categories, variants, weights, and multiple barcodes. Connect scales and scanners for seamless checkout'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_7.png'
            },
            {
                'title': _lt('Self-Service & Merchandising'),
                'description': _lt('Enable self-order kiosks, customer displays, and print-ready receipts with customized info'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_8.png'
            },
            {
                'title': _lt('Unified Inventory & Accounting Integration'),
                'description': _lt('Immediately update stock across locations and push payments straight into your financial ledger'),
                'image': '/dekad_website/static/src/img/migrated/apps/point-of-sale/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-puzzle-piece',
                    'title': _lt('Fully Integrated & Cloud-Connected'),
                    'description': _lt('From POS to accounts, inventory, and CRM—everything updates in real time, with no manual syncing needed.')
                },
                {
                    'icon': 'fa-arrow-up',
                    'title': _lt('Fast Deployment & Ease of Use'),
                    'description': _lt('Your team will master it in minutes. We help you customize layouts, user roles, and hardware setup for your specific needs.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable to Any Business'),
                    'description': _lt('Single-shop or franchise? Multi-device and multi-store support scales with your growth without added tools.')
                },
                {
                    'icon': 'fa-lock',
                    'title': _lt('Secure & Compliance-Ready'),
                    'description': _lt('With PIN-protected cashiers, audit logs, and reliable offline reconciliation, you stay compliant and controlled.')
                },
                {
                    'icon': 'fa-user-o',
                    'title': _lt('Customer-Centric Loyalty Tools'),
                    'description': _lt('Create coupons, gift cards, and reward programs to incentivize repeat visits and increase spend.')
                },
                {
                    'icon': 'fa-retweet',
                    'title': _lt('Real-Time Insights'),
                    'description': _lt('Track sales trends, cashier performance, and stock levels instantly through dashboards and reports.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Support from Dekad Experts'),
                    'description': _lt('We handle everything—setup, training, configuration, and ongoing support to ensure lasting success.')
                }
            ]
        }
    },
    'subscriptions': {
        'slug': 'subscriptions',
        'name': _lt('Subscriptions management'),
        'subtitle': _lt('Streamlined Subscription Billing & Management'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/subscriptions/cover_bg.webp',
        'overview': {
            'title': _lt('Seamlessly manage recurring revenue with intelligent automation'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Subscriptions module simplifies the full subscriber lifecycle. From automated billing and renewals to flexible contract management and customer portals, you get everything needed to scale recurring services. Let your team focus on engagement while recurring invoices, payments, taxes, and analytics are handled seamlessly.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Automated Recurring Billing'),
                'description': _lt('Set up recurring plans—monthly, yearly, or custom—and invoices are automatically issued and processed on schedule'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_2.png'
            },
            {
                'title': _lt('Self-Service Customer Portal'),
                'description': _lt('Your clients can manage contracts, update details, renew, upgrade/downgrade plans, and cancel—all without logging in manually'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_3.png'
            },
            {
                'title': _lt('Integrated One-off & Recurring Sales'),
                'description': _lt('Sell both subscription and one-time products on the same order and manage billing from a unified platform'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_4.png'
            },
            {
                'title': _lt('Flexible Plan & Contract Templates'),
                'description': _lt('Use reusable templates for pricing, options, and billing cycles—speeding up subscription creation'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_5.png'
            },
            {
                'title': _lt('Advanced Analytics & Cohort Insights'),
                'description': _lt('Monitor metrics like MRR, churn, expansion, renewal rates, LTV, and forecast future growth with built-in dashboards'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_6.png'
            },
            {
                'title': _lt('Upsell, Renewals & Cancellation Controls'),
                'description': _lt('Enable automated renewal reminders; let customers upsell or cancel with reason capture—all tracked in the system'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_7.png'
            },
            {
                'title': _lt('Robust Tax & Payment Rules'),
                'description': _lt('Tax is calculated in real-time based on customer location, with automated payment reminders and support for saved payment methods'),
                'image': '/dekad_website/static/src/img/migrated/apps/subscriptions/image_8.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-gears',
                    'title': _lt('Hands-Off Billing Automation'),
                    'description': _lt('Set the plan once, and recurring invoices, payments, and analytics run automatically—no manual intervention.')
                },
                {
                    'icon': 'fa-retweet',
                    'title': _lt('Customer Empowerment & Retention'),
                    'description': _lt("Let customers manage their own plans and contracts, reducing churn and freeing up your team's time.")
                },
                {
                    'icon': 'fa-external-link-square',
                    'title': _lt('Growth-Focused Insights'),
                    'description': _lt('Track key subscription metrics and forecast trends to make data-driven decisions and boost revenue.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Subscription Businesses'),
                    'description': _lt('Suitable for SaaS, service providers, memberships, and goods—supporting complex cycles, multi-product bundles, and custom intervals.')
                }
            ]
        }
    },
    'rental': {
        'slug': 'rental',
        'name': _lt('Rental'),
        'subtitle': _lt('A long-term solution for short-term deals'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/rental/cover_bg.webp',
        'overview': {
            'title': _lt('Manage rentals, schedules, and agreements—all from one integrated platform'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Rental module gives you complete control over your rental business. Whether you rent equipment, furniture, or machinery, this powerful tool handles everything—from quotes and bookings to returns and invoicing. With built-in scheduling, availability checks, digital contracts, and seamless ERP integration, you can simplify operations, avoid conflicts, and enhance customer satisfaction.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/rental/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Online Booking & Reservations'),
                'description': _lt('Enable customers to reserve and pay for rentals via your website—automatically updating availability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_2.webp'
            },
            {
                'title': _lt('Time-Based Pricing & Rate Management'),
                'description': _lt('Set custom pricing per hour, day, week, or month—and support delayed fees automatically.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_3.webp'
            },
            {
                'title': _lt('Smart Scheduling Tools'),
                'description': _lt('Define unavailable days, padding times, and minimum rental durations to prevent overlap.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_4.png'
            },
            {
                'title': _lt('Digital Agreements & Signatures'),
                'description': _lt('Upload rental contracts and request e-signatures before order confirmation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_5.png'
            },
            {
                'title': _lt('Pickup & Return Tracking'),
                'description': _lt('Easily manage pickup/drop-off workflows, including PDF receipts and status updates.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_6.png'
            },
            {
                'title': _lt('Deposit & Delay Fee Handling'),
                'description': _lt('Collect and refund security deposits; apply automatic charges for overdue returns.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_7.png'
            },
            {
                'title': _lt('Dynamic Dashboard & Reporting'),
                'description': _lt('Monitor rental status, invoicing levels, and item usage with intuitive analytics.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_8.png'
            },
            {
                'title': _lt('Full ERP Integration'),
                'description': _lt('Connect seamlessly with Inventory, Sales, Invoicing, Subscriptions, Maintenance, and Helpdesk.'),
                'image': '/dekad_website/static/src/img/migrated/apps/rental/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check',
                    'title': _lt('One System, No Gaps'),
                    'description': _lt('Manage quotes, stock, contracts, invoices, and support—all in your ERP, without manual imports.')
                },
                {
                    'icon': 'fa-gear',
                    'title': _lt('Optimized Operations'),
                    'description': _lt('Avoid double-booking, track assets, and maintain availability with smart scheduling tools.')
                },
                {
                    'icon': 'fa-shield',
                    'title': _lt('Boost Customer Confidence'),
                    'description': _lt('Offer online reservations, secure deposits, and e-signed contracts to build trust and professionalism.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Future-Proofed for Growth'),
                    'description': _lt('Whether renting a few or thousands of items, our system scales as you grow across locations and teams.')
                }
            ]
        }
    },
    'employee': {
        'slug': 'employee',
        'name': _lt('Employee'),
        'subtitle': _lt('A new headquarters for all your employee data—beyond a simple directory'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/employee/cover_bg.webp',
        'overview': {
            'title': _lt('Centralize personal info, attendance, contracts, skills, and hierarchy in a single unified system.'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Employees module empowers your HR team with a modern, secure platform to manage staff details, track attendance, handle contracts, and support growth. Whether you're onboarding new hires, evaluating performance, or organizing teams, it all happens cohesively and efficiently.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/employee/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation'
        },
        'key_features': [
            {
                'title': _lt('Comprehensive Employee Profiles'),
                'description': _lt('Store personal, professional, and contract info—resumes, skills, certifications, emergency contacts—all in one place.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_2.webp'
            },
            {
                'title': _lt('Organizational Hierarchy & Visibility'),
                'description': _lt('View your team structure at a glance, filter by department, job role, or company, and group employees by presence or skills.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_3.png'
            },
            {
                'title': _lt('Attendance & Time-Off Tracking'),
                'description': _lt('Monitor employee presence, request approvals, view absences, and enforce PTO policies—all within the HR workspace.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_4.png'
            },
            {
                'title': _lt('Document & Contract Management'),
                'description': _lt('Upload signed contracts, store documents, request e-signatures, and maintain secure access to sensitive records.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_5.png'
            },
            {
                'title': _lt('Skill Tracking & Appraisals'),
                'description': _lt('Manage skills and certifications, set goals, and run performance reviews through appraisal tools integrated within employee profiles.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_6.webp'
            },
            {
                'title': _lt('Activity Scheduling & Onboarding'),
                'description': _lt('Assign tasks, track training steps, set reminders, and streamline the onboarding/offboarding process with smart activity planning.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_7.png'
            },
            {
                'title': _lt('User Privacy & Role-based Access'),
                'description': _lt('Control who can see sensitive info like visas, emergency contacts, and payroll data with finely-tuned access settings.'),
                'image': '/dekad_website/static/src/img/migrated/apps/employee/image_8.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-shield',
                    'title': _lt('Unified HR-ERP Experience'),
                    'description': _lt('All HR activities—from recruitment to payroll—are built on the same Odoo platform, integrating with attendance, project, and accounting modules seamlessly.')
                },
                {
                    'icon': 'fa-gear',
                    'title': _lt('Secure & Compliance-Ready'),
                    'description': _lt('Protect sensitive data with permission settings and maintain audit trails for contracts and signatures, ensuring full compliance with regulations.')
                },
                {
                    'icon': 'fa-wrench',
                    'title': _lt('Smart Insights & Reporting'),
                    'description': _lt('From retail to manufacturing, we adapt your finance tools to your specific business operations.')
                },
                {
                    'icon': 'fa-refresh',
                    'title': _lt('Modular & Scalable'),
                    'description': _lt('We don’t just install software—we partner with you for implementation, training, and ongoing optimization.')
                },
                {
                    'icon': 'fa-shield',
                    'title': _lt('Expert HR Implementation'),
                    'description': _lt('Our HR specialists configure workflows, build onboarding/offboarding pipelines, train users, and ensure adoption across your organization.')
                }
            ]
        }
    },
    'recruitment': {
        'slug': 'recruitment',
        'name': _lt('Recruitment'),
        'subtitle': _lt('The all‑in‑one recruitment platform to hire the best—faster'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/recruitment/cover_bg.png',
        'overview': {
            'title': _lt('Centralize all job roles, applicants, and activities in one powerful dashboard.'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Recruitment module transforms hiring into a strategic, organized, and efficient process. Tailored stages, integrated communications, and automatic actions ensure candidates move smoothly through your pipeline—freeing your team to focus on top talent and culture fit.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Centralized Job & Applicant Dashboard'),
                'description': _lt('See all job vacancies, application counts, and next steps at a glance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_2.webp'
            },
            {
                'title': _lt('Customizable Pipelines & Automated Actions'),
                'description': _lt('Drag and drop candidate cards, trigger emails at each stage, and build workflow logic tailored to your hiring style.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_3.webp'
            },
            {
                'title': _lt('Multi‑Channel Job Publishing'),
                'description': _lt('Publish openings on your website or job boards like Monster.com with a single click—and track source performance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_4.png'
            },
            {
                'title': _lt('Smart Resume Parsing (OCR)'),
                'description': _lt('Automatically extract contact details from uploaded CVs and attach resumes to applicant profiles.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_5.png'
            },
            {
                'title': _lt('Candidate Scheduling & Calendar Sync'),
                'description': _lt('Allow candidates to book interviews via your availability; sync with Google or Outlook.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_6.webp'
            },
            {
                'title': _lt('Offer Management & e‑Signing'),
                'description': _lt('Generate offers, set expiry dates, and let candidates review and sign electronically—then convert them into employees instantly.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_7.webp'
            },
            {
                'title': _lt('Recruitment Analytics & Metrics'),
                'description': _lt('Get detailed insights into time‑to‑hire, source channels, pipeline health, and hiring efficiency.'),
                'image': '/dekad_website/static/src/img/migrated/apps/recruitment/image_8.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-align-center',
                    'title': _lt('One Unified HR System'),
                    'description': _lt('Our Recruitment is native to Odoo — when candidates are hired, they automatically become employees in the HR module, with no manual transfers.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Efficient, Data-Driven Hiring'),
                    'description': _lt('Visual pipelines and automated actions reduce admin work and improve selection accuracy and speed.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Candidate-Friendly Process'),
                    'description': _lt('Allow applicants to self‑schedule, submit CVs, and sign offers online, enhancing the candidate experience.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable & Configurable'),
                    'description': _lt('Customize pipelines, stages, activity types, job types, and offer templates to match any hiring process or business complexity.')
                },
                {
                    'icon': 'fa-shield',
                    'title': _lt('Secure & Compliant'),
                    'description': _lt('Store applicant data, contracts, and communications in one protected, audit-ready system.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Implementation by Dekad'),
                    'description': _lt('We configure your workflows, integrate multi-channel posting, set up analytics, and train your team for peak recruiting performance.')
                }
            ]
        }
    },
    'time-off-attendance': {
        'slug': 'time-off-attendance',
        'name': _lt('Time Off & Attendance'),
        'subtitle': _lt('Harness the power of centralized leave requests and real-time check-ins to streamline HR operations, maintain compliance, and improve employee satisfaction.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/cover_bg.webp',
        'overview': {
            'title': _lt('Manage time off and attendance with accuracy and ease'),
            'paragraphs': [
                _lt('At Dekad Software Solutions, we bring you a unified HR toolset that automates leave management, attendance tracking, and reporting. Whether managing PTO, sick days, or back-to-back shifts—and integrating with payroll and compliance—our solution enhances transparency and efficiency.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Comprehensive Time Off Types & Accruals'),
                'description': _lt('Choose from pre‑configured leave types like Paid, Sick, Unpaid, or add custom ones. Manage accruals, allocations, and custom policies.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_2.png',
            },
            {
                'title': _lt('Simple Request & Approval Workflow'),
                'description': _lt('Employees can submit, cancel, or reschedule time off through the portal. Managers see requests in an intuitive dashboard for fast approval.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_3.webp',
            },
            {
                'title': _lt('Holiday & Stress Day Planning'),
                'description': _lt('Configure public holidays and blackout dates to automatically block leave on predetermined days.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_4.png',
            },
            {
                'title': _lt('Team Calendar & Usage Overview'),
                'description': _lt("A calendar view highlights who’s out, who’s approved, and available PTO balances—all colour-coded for clarity."),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_5.webp',
            },
            {
                'title': _lt('Attendance Kiosk & Check‑In/Out'),
                'description': _lt('Employees log hours via kiosk mode or directly in the database. Managers gain visibility into presence and availability in real time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_6.png',
            },
            {
                'title': _lt('Overtime & Auto Check‑Out'),
                'description': _lt('Configure extra hours, set grace periods, and auto-check-out late employees for better time management.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_7.png',
            },
            {
                'title': _lt('Smart Reporting & Insights'),
                'description': _lt('Access pivot, list, and chart reports for PTO usage by employee/type and analyze overtime, absenteeism, and usage trends.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_8.webp',
            },
            {
                'title': _lt('Role-Based Access & Notifications'),
                'description': _lt('Configure approvers and access rights, receive instant notifications, and keep communication streamlined across HR teams.'),
                'image': '/dekad_website/static/src/img/migrated/apps/time-off-attendance/image_9.png',
            },
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa fa-puzzle-piece',
                    'title': _lt('Unified Leave & Attendance Management'),
                    'description': _lt('Integrate leave requests and attendance logs within a single Odoo platform—eliminating manual sync, spreadsheets, and missed entries.'),
                },
                {
                    'icon': 'fa fa-id-badge',
                    'title': _lt('Staff Self-Service'),
                    'description': _lt('Your team can request leave, check balances, and log hours from any device—reducing HR overload and improving employee experience.'),
                },
                {
                    'icon': 'fa fa-check',
                    'title': _lt('Compliance & Policy Control'),
                    'description': _lt('Customize leave policies—negative balances, blackout days, approvers—while maintaining clear audit trails and reporting.'),
                },
                {
                    'icon': 'fa fa-line-chart',
                    'title': _lt('Better Productivity & Planning'),
                    'description': _lt('With calendar visibility and usage reporting, managers plan shifts effectively and reduce overlap or understaffing.'),
                },
                {
                    'icon': 'fa fa-expand',
                    'title': _lt('Scalable Across Organizations'),
                    'description': _lt('Works with multi-company, department, and user-role setups—supporting both small teams and enterprise structures.'),
                },
                {
                    'icon': 'fa fa-thumbs-o-up',
                    'title': _lt('Expert Deployment by Dekad'),
                    'description': _lt('We support policy setup, kiosk deployment, notification templates, and reporting dashboards to ensure adoption and compliance.'),
                },
            ],
        },
    },
    'appraisals': {
        'slug': 'appraisals',
        'name': _lt('Appraisal and Employee Evaluation'),
        'subtitle': _lt('Run structured reviews, gather feedback, and track development—all from one centralized platform.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/appraisals/cover_bg.webp',
        'overview': {
            'title': _lt('Performance reviews that build success and sharpen skills'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Appraisals module transforms employee evaluation into a transparent, continuous process. Built-in self-assessment, manager feedback, goal tracking, and 360° review make it ideal for driving performance, growth, and engagement.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation'
        },
        'key_features': [
            {
                'title': _lt('Automated Appraisal Plans'),
                'description': _lt('Schedule appraisals—onboarding, periodic, or custom—triggered automatically by date or tenure.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_2.png'
            },
            {
                'title': _lt('360° Feedback Collection'),
                'description': _lt('Invite peer insights alongside self and manager reviews for a well-rounded evaluation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_3.png'
            },
            {
                'title': _lt('Structured Templates & Custom Surveys'),
                'description': _lt('Use role-specific appraisal forms or tailor your own using reusable templates.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_4.png'
            },
            {
                'title': _lt('Goal Setting & Progress Linkage'),
                'description': _lt('Define goals, set deadlines, and seamlessly link progress metrics to each appraisal session.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_5.png'
            },
            {
                'title': _lt('Manager and Employee Self-Assessments'),
                'description': _lt('Employees complete self-reviews before managers provide their feedback for transparent alignment.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_6.png'
            },
            {
                'title': _lt('Skill Tracking & Evolution Reports'),
                'description': _lt('Capture skill levels over time and generate reports on skill growth and gaps.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_7.png'
            },
            {
                'title': _lt('Integrated Review Meetings & Notes'),
                'description': _lt('Schedule meetings directly from the app, add private notes, and finalize ratings—all within your workflow.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_8.png'
            },
            {
                'title': _lt('Performance Dashboards'),
                'description': _lt('Analyze appraisal status, completion rate, and milestones using Kanban, calendar, Gantt, graph, and pivot views.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appraisals/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-arrows',
                    'title': _lt('Unified HR Experience'),
                    'description': _lt('Your appraisal process connects directly with recruitment, attendance, time-off, and payroll—no data silos.')
                },
                {
                    'icon': 'fa-puzzle-piece',
                    'title': _lt('Fully Configurable to Your Needs'),
                    'description': _lt('We tailor appraisal templates, feedback loops, review cycles, and evaluation scales to suit your business culture.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Culture of Continuous Improvement'),
                    'description': _lt('Encourage performance visibility, regular dialogs, and measurable progress for genuine team development.')
                },
                {
                    'icon': 'fa-area-chart',
                    'title': _lt('Data-Driven Performance Management'),
                    'description': _lt('Use real-time metrics—skill gaps, goal attainment, cycle histories—to guide training and retention decisions.')
                },
                {
                    'icon': 'fa-shield',
                    'title': _lt('Secure & Compliant Reviews'),
                    'description': _lt('Role-based access and audit trails ensure confidential data stays protected and compliant.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Support from Dekad'),
                    'description': _lt('We implement your automation strategy, configure feedback processes, and support manager training for optimal outcomes.')
                }
            ]
        }
    },
    'fleet-management': {
        'slug': 'fleet-management',
        'name': _lt('Fleet Management'),
        'subtitle': _lt('Manage vehicles, drivers, contracts, maintenance, and costs—all through a single, user-friendly interface.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/fleet-management/cover_bg.webp',
        'overview': {
            'title': _lt('Efficient, Integrated Fleet Management in One Dashboard'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Fleet module empowers you to oversee your vehicle assets with ease. Track every detail—from registration and insurance to fuel usage and service logs—while ensuring seamless integration with accounting, HR, and expense systems. It’s everything you need for smart, cost-effective fleet operations.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Vehicle & Driver Profiles'),
                'description': _lt('Maintain detailed records—model, engine specs, insurance, and assigned drivers.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_2.png'
            },
            {
                'title': _lt('Customizable Fleet Structure'),
                'description': _lt('Organize vehicles by categories, models, manufacturers, and acquisition stages.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_3.png'
            },
            {
                'title': _lt('Complete Contract & Insurance Management'),
                'description': _lt('Track leasing, service agreements, and insurance. Receive automated renewal alerts.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_4.png'
            },
            {
                'title': _lt('Fuel & Odometer Tracking'),
                'description': _lt('Log mileage and fuel use per vehicle. Identify cost-saving opportunities and flag anomalies.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_5.png'
            },
            {
                'title': _lt('Maintenance & Service Logs'),
                'description': _lt('Record repairs with vendor details, service costs, and schedule recurring maintenance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_6.png'
            },
            {
                'title': _lt('Cost Reporting & Analytics'),
                'description': _lt('Get detailed insights per vehicle or fleet—maintenance, fuel, contracts—via pivot tables, charts, and exports.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_7.png'
            },
            {
                'title': _lt('Seamless Integrations'),
                'description': _lt('All entries sync to Accounting, HR (for driver costs), Expenses, and Project modules automatically.'),
                'image': '/dekad_website/static/src/img/migrated/apps/fleet-management/image_8.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-arrows',
                    'title': _lt('Unified ERP Connection'),
                    'description': _lt('No standalone platforms—fleet control flows into HR, finance, and project operations.')
                },
                {
                    'icon': 'fa-dollar',
                    'title': _lt('Proactive Cost Control'),
                    'description': _lt('With mileage, fuel, and maintenance analytics, you spot inefficiencies, reduce downtime, and optimize vehicle life cycles.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Compliance & Risk Reduction'),
                    'description': _lt('Maintain audit-ready records for insurance, contracts, and services—backed by automated reminders.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Tailored for Your Fleet Size'),
                    'description': _lt('From a small company car list to full vehicle pools, the solution scales with your needs.')
                },
                {
                    'icon': 'fa-automobile',
                    'title': _lt('Enhanced Asset Visibility'),
                    'description': _lt('Detailed dashboards on vehicle status, expenses, and assignments aid faster decisions.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Support & Configuration from Dekad'),
                    'description': _lt('We set up vehicle policies, custom categories, reminders, and provide training for smooth adoption and ongoing optimization.')
                }
            ]
        }
    },
    'inventory-management': {
        'slug': 'inventory-management',
        'name': _lt('Inventory Management'),
        'subtitle': _lt('Manage warehouses, track stock in real time, and automate replenishment using FIFO, landed cost, and multi-location strategies—all within a single, integrated system.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/inventory-management/cover_bg.webp',
        'overview': {
            'title': _lt('Revolutionary double-entry inventory for modern warehouses'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Inventory module is designed to streamline your entire supply chain—from procurement to delivery. Whether you're running a single warehouse or multiple locations, our system’s real-time visibility, rules-based automation, and seamless ERP integration help you optimize stock levels, reduce waste, and improve customer satisfaction.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Expiration Date Alerts & FIFO/FEFO Tracking'),
                'description': _lt('Automatically prioritize items by expiry or FIFO rules and receive removal reminders.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_2.png'
            },
            {
                'title': _lt('Multi-Warehouse & Location Management'),
                'description': _lt('Define warehouses, zones, and storage rules with support for cross-docking and dropshipping.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_3.png'
            },
            {
                'title': _lt('Advanced Product Tracking'),
                'description': _lt('Manage serial numbers, lot traceability, and custom fields for full compliance and traceability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_4.png'
            },
            {
                'title': _lt('Intelligent Reordering & Lead Times'),
                'description': _lt('Use min-max levels, replenish on order, and schedule blanket orders for auto governance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_5.png'
            },
            {
                'title': _lt('Barcode & Hardware Integration'),
                'description': _lt('Use scanners, scales, and IoT devices (e.g. Zebra, Mettler Toledo) to streamline pick & pack workflows.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_6.png'
            },
            {
                'title': _lt('Embedded Shipping & Label Printing'),
                'description': _lt('Generate shipping labels, calculate costs, and integrate with carriers like FedEx, DHL, UPS, and more.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_7.png'
            },
            {
                'title': _lt('Landed Costs & Real-Time Valuation'),
                'description': _lt('Include duties, freight, and fees in product cost, with real-time accounting entries.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_8.png'
            },
            {
                'title': _lt('Smart Reporting & Forecasting'),
                'description': _lt('Get actionable insights with stock moves, aging reports, stock value dashboards, and predictive stock levels.'),
                'image': '/dekad_website/static/src/img/migrated/apps/inventory-management/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Complete ERP Integration'),
                    'description': _lt('Inventory connects seamlessly with Sales, Purchase, Manufacturing, Accounting, eCommerce, and more—no manual syncs needed.')
                },
                {
                    'icon': 'fa-retweet',
                    'title': _lt('Optimize Stock, Cut Costs'),
                    'description': _lt('Automate replenishment and expiration tracking to reduce waste, holding costs, and stockouts.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Traceability & Compliance'),
                    'description': _lt('Use lot/serial tracking and full audit trails to meet industry regulations and operational audits.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Every Business'),
                    'description': _lt('Built for warehouses of any size, with support for complex layouts and multi-warehouse operations.')
                },
                {
                    'icon': 'fa-mobile-phone',
                    'title': _lt('Mobile & Hardware Enabled'),
                    'description': _lt('Equip your warehouse with handheld devices and scales for efficient, error-free logistics.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Support from Dekad'),
                    'description': _lt('Our team configures warehouse rules, trains staff, customizes reporting, and ensures lasting ROI.')
                }
            ]
        }
    },
    'manufacturing': {
        'slug': 'manufacturing',
        'name': _lt('Manufacturing'),
        'subtitle': _lt('Streamline your operations with real-time scheduling, shop‑floor management, quality checks, and traceability—all within your ERP.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/manufacturing/cover_bg.webp',
        'overview': {
            'title': _lt('Efficient, scalable manufacturing—from planning to production and quality control'),
            'paragraphs': [
                _lt('At Dekad Software Solutions, our Manufacturing module empowers you to automate end-to-end production workflows. Seamlessly manage work orders, BOMs, maintenance, quality control, and resource allocation—ensuring smooth and compliant manufacturing operations prepared for scale.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Manufacturing Orders & Work Orders'),
                'description': _lt('Handle both batch and assembly-line operations with editable orders and shop-floor tracking.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_2.png'
            },
            {
                'title': _lt('Dynamic Scheduling & Capacity Planning'),
                'description': _lt('Visualize your MPS on a Gantt chart, manage finite capacity, and adjust production based on availability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_3.png'
            },
            {
                'title': _lt('Multi-Level Bills of Materials (BoMs)'),
                'description': _lt('Create multi-level and multi-routing BoMs with version control and optional subassemblies.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_4.png'
            },
            {
                'title': _lt('Barcode & IoT Integration'),
                'description': _lt('Enable shop-floor scanning, workstation instructions, and IoT integrations for tablets and devices.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_5.png'
            },
            {
                'title': _lt('Quality Control & Traceability'),
                'description': _lt('Embed quality checks at each manufacturing stage and track lot/serial numbers with full historical traceability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_6.png'
            },
            {
                'title': _lt('Maintenance & Repair Orders'),
                'description': _lt('Launch maintenance tasks automatically from workstations and track repair orders on the same platform.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_7.png'
            },
            {
                'title': _lt('OEE Reporting & Cost Analysis'),
                'description': _lt('Analyze equipment performance, scrap data, labor costs, and material usage through rich dashboards.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_8.png'
            },
            {
                'title': _lt('Product Lifecycle Management (PLM)'),
                'description': _lt('Control Engineering Change Orders (ECOs), track revisions, and attach documents directly to BoMs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_9.gif'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All-in-One ERP Integration'),
                    'description': _lt('Sync Manufacturing with Inventory, Purchase, Maintenance, Quality, Accounting, and Sales for seamless operations.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Visual Planning for Rapid Decisions'),
                    'description': _lt('Use Gantt-based scheduling to reduce downtime, handle rush orders, and maintain production flow.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Operational Efficiency & Transparency'),
                    'description': _lt('Real-time shop-floor tracking and quality alerts help improve throughput and reduce delays.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Compliance & Full Traceability'),
                    'description': _lt('Automatically track serials, versions, quality checkpoints, and maintenance logs for audit-ready operations.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Growth'),
                    'description': _lt('Support simple to complex production environments—multi-location, multi-level, and multi-device—without friction.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Implementation from Dekad'),
                    'description': _lt('We handle BoM setup, PLM configuration, IoT integration, and staff training to ensure smooth adoption and continuous improvement.')
                }
            ]
        }
    },
    'plm': {
        'slug': 'plm',
        'name': _lt('Product Lifecycle Management (PLM)'),
        'subtitle': _lt('Centralize Engineering Change Orders (ECOs), BoM versions, and design documentation in one collaborative platform—ensuring clear communication, traceability, and no errors during production.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/plm/cover_bg.webp',
        'overview': {
            'title': _lt('Streamline product innovation and version control'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our PLM module enhances your product development lifecycle. You can propose changes, get approvals, revert or rebase revisions, and keep your manufacturing aligned with the latest design—all without disrupting ongoing production.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/plm/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Engineering Change Orders (ECOs)'),
                'description': _lt('Create isolated ECO workflows to test and implement product updates, maintaining production stability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/plm/image_2.gif'
            },
            {
                'title': _lt('BoM Version Management'),
                'description': _lt('Edit BoMs—including materials, operations, and CAD files—and activate new versions without confusion.'),
                'image': '/dekad_website/static/src/img/migrated/apps/plm/image_3.png'
            },
            {
                'title': _lt('Compare & Merge Versions'),
                'description': _lt('Track differences between BoM versions, resolve conflicts, and apply changes selectively using smart rebase tools.'),
                'image': '/dekad_website/static/src/img/migrated/apps/plm/image_4.png'
            },
            {
                'title': _lt('Document Management & Feedback'),
                'description': _lt('Attach drawings, worksheets, or PDFs and collect feedback during production—automatically initiating new ECOs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/plm/image_5.png'
            },
            {
                'title': _lt('Approval Workflows & Collaboration'),
                'description': _lt('Set customizable ECO stages, approval roles, and milestone tracking—with internal chatter for coordination.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_6.png'
            },
            {
                'title': _lt('Traceability & Reporting'),
                'description': _lt('View detailed logs of all ECOs, effective dates, and BoM history for full auditability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/manufacturing/image_7.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All-in-One ERP Integration'),
                    'description': _lt('Sync Manufacturing with Inventory, Purchase, Maintenance, Quality, Accounting, and Sales for seamless operations.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Visual Planning for Rapid Decisions'),
                    'description': _lt('Use Gantt-based scheduling to reduce downtime, handle rush orders, and maintain production flow.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Operational Efficiency & Transparency'),
                    'description': _lt('Real-time shop-floor tracking and quality alerts help improve throughput and reduce delays.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Compliance & Full Traceability'),
                    'description': _lt('Automatically track serials, versions, quality checkpoints, and maintenance logs for audit-ready operations.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Growth'),
                    'description': _lt('Support simple to complex production environments—multi-location, multi-level, and multi-device—without friction.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Implementation from Dekad'),
                    'description': _lt('We handle BoM setup, PLM configuration, IoT integration, and staff training to ensure smooth adoption and continuous improvement.')
                }
            ]
        }
    },
    'maintenance': {
        'slug': 'maintenance',
        'name': _lt('Maintenance'),
        'subtitle': _lt('Track preventive and corrective maintenance requests, schedule tasks on a smart calendar, and monitor machine health—all within a unified ERP environment.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/maintenance/cover_bg.webp',
        'overview': {
            'title': _lt('Extend equipment lifespan and reduce downtime'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Maintenance module empowers your operations team to keep equipment in top form. From request handling to repair logging and statistical monitoring (like MTBF/MTTR), every maintenance activity is logged, scheduled, and analyzed—ensuring efficiency, transparency, and integration with your Manufacturing and Inventory processes.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/plm/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Maintenance Requests & Workflow'),
                'description': _lt('Log corrective or preventive tasks per equipment or work center, then track progress through configurable stages (done, scrap, etc.)'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image.png'
            },
            {
                'title': _lt('Intuitive Calendar & Kanban Views'),
                'description': _lt('Schedule tasks visually via calendar or Kanban board, with drag-and-drop functionality and activity filters'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image_2.gif'
            },
            {
                'title': _lt('Equipment & Work Center Management'),
                'description': _lt('Maintain detailed profiles—registration, warranty, categories, technician assignments—with real-time metrics like MTBF/MTTR'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image_3.png'
            },
            {
                'title': _lt('Preventive Maintenance Automation'),
                'description': _lt('Automatically schedule recurring servicing based on usage data or time intervals, preventing breakdowns before they occur'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image_4.png'
            },
            {
                'title': _lt('Technician Teams & Role Assignment'),
                'description': _lt('Define maintenance teams, assign jobs to technicians, and control task ownership—with reminders and internal chatter'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image_5.png'
            },
            {
                'title': _lt('Advanced Reporting & KPIs'),
                'description': _lt('Access dashboards and reports with MTBF/MTTR trends, equipment downtime, task status, and action-backed insights'),
                'image': '/dekad_website/static/src/img/migrated/apps/maintenance/image_6.gif'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Unified Equipment Intelligence'),
                    'description': _lt('From breakdowns to repairs, every maintenance action flows into your ERP—no guesswork, no spreadsheets.')
                },
                {
                    'icon': 'fa-calendar',
                    'title': _lt('Proactive Maintenance Management'),
                    'description': _lt('Prevent production halts with scheduled servicing, real-time equipment monitoring, and automatic alerts.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Operational Clarity'),
                    'description': _lt('Visual dashboards and real-time logs keep production supervisors and maintenance teams in sync.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Reduce Costs & Downtime'),
                    'description': _lt('By tracking MTBF and MTTR, you’ll spot inefficiencies and optimize equipment usage with confidence.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable Across Shifts & Sites'),
                    'description': _lt('Manage multiple teams, equipment pools, and workflows with the same platform—designed to grow.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Dedicated Support from Dekad'),
                    'description': _lt('We help configure equipment profiles, maintenance intervals, team structures, calendar layouts, and reporting—then train your teams to maintain optimal performance.')
                }
            ]
        }
    },
    'quality-management': {
        'slug': 'quality-management',
        'name': _lt('Quality management'),
        'subtitle': _lt('Automate inspections across manufacturing and inventory flows, raise quality alerts, and manage corrective actions—all within your ERP.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/quality-management/cover_bg.webp',
        'overview': {
            'title': _lt('Ensure product consistency and catch defects before they reach customers'),
            'paragraphs': [
                _lt('At Dekad Software Solutions, our Quality module empowers teams to enforce quality standards seamlessly.'),
                _lt('From defining control points to documenting root causes and corrective steps, this integrated tool enables proactive quality management and continuous improvement across your operations.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation'
        },
        'key_features': [
            {
                'title': _lt('Quality Control Points & Automated Checks'),
                'description': _lt('Define inspection points on manufacturing orders, delivery or receipt operations, and automatically trigger checks at the right stage.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_2.png'
            },
            {
                'title': _lt('Quality Alerts & Kanban Tracking'),
                'description': _lt('Raise alerts when checks fail, assign priorities, and move them through review stages in a visual Kanban interface.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_3.webp'
            },
            {
                'title': _lt('Custom Inspection Types & Worksheets'),
                'description': _lt('Choose from pass/fail, measurement, photo attachment, or instruction-based checks—and configure interactive worksheets for easy data capture.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_4.webp'
            },
            {
                'title': _lt('Quality Teams & Roles'),
                'description': _lt('Create dedicated quality teams and assign tasks or alerts to specific roles—ensuring ownership and accountability.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_5.png'
            },
            {
                'title': _lt('Quality Reporting & Insight Dashboards'),
                'description': _lt('Analyze inspection frequency, failure reasons, and alert resolution with detailed reports and charts for continuous improvement.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_6.webp'
            },
            {
                'title': _lt('Full Supply‑Chain Integration'),
                'description': _lt('Quality checks are embedded within Manufacturing, Inventory, PLM, and Maintenance operations—no extra steps required.'),
                'image': '/dekad_website/static/src/img/migrated/apps/quality-management/image_7.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Embedded Quality Across Operations'),
                    'description': _lt("Quality control isn't an afterthought—it's built into your production and warehouse workflows for real-time assurance.")
                },
                {
                    'icon': 'fa-calendar',
                    'title': _lt('Immediate Defect Detection & Response'),
                    'description': _lt('Alerts trigger root cause analysis and corrective actions before issues escalate, preserving product integrity.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Custom Checks for Any Scenario'),
                    'description': _lt('From batch inspections to component-level measures, tailor both check types and workflows to your needs.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Accountability Through Teams'),
                    'description': _lt('Define roles, assign tasks, and track outputs with clear responsibility and traceability.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Metrics-Driven Improvement'),
                    'description': _lt('Use reporting to identify defect trends, reduce waste, and boost overall quality performance.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Quality Setup by Dekad'),
                    'description': _lt('We’ll configure control points, alert handling, worksheets, and dashboards to match your exact operational needs—and train your team for adoption.')
                }
            ]
        }
    },
    'purchase': {
        'slug': 'purchase',
        'name': _lt('Purchase'),
        'subtitle': _lt('Automate your sourcing—from RFQs to supplier bills—while synchronizing with stock levels, multiple companies, and accounting.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/purchase/cover_bg.webp',
        'overview': {
            'title': _lt('Streamlined Procurement & Vendor Management'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we enable smarter purchasing cycles. Our Purchase module allows you to streamline vendor relationships, ensure accurate cost control, and maintain full procurement oversight with transparency and efficiency.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/purchase/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Automated RFQs & Purchase Orders'),
                'description': _lt('Generate requests for quotation or purchase orders automatically based on stock rules, vendor pricelists, or manual triggers.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_2.webp'
            },
            {
                'title': _lt('Three-Way Matching Control'),
                'description': _lt('Verify that supplier bills match ordered quantities and received goods before payment is issued.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_3.png'
            },
            {
                'title': _lt('Blanket Orders & Purchase Tenders'),
                'description': _lt('Negotiate long-term supplier agreements and automatically manage recurring orders.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_4.png'
            },
            {
                'title': _lt('Vendor Management & Pricelists'),
                'description': _lt('Maintain vendor profiles, compare offers, and utilize vendor-specific pricelists for better negotiation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_5.png'
            },
            {
                'title': _lt('Multi-Company & Multi-Currency Support'),
                'description': _lt('Centralize procurement across entities with unified bills, currency handling, and reconciliation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_6.webp'
            },
            {
                'title': _lt('Variant & Packaging Controls'),
                'description': _lt('Handle product variants, units of measure, and packaging details directly in purchase documents.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_7.webp'
            },
            {
                'title': _lt('Integrated Reordering & Inventory Sync'),
                'description': _lt('Align ordering with stock levels, sales, and manufacturing needs through synchronized ERP rules.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_8.png'
            },
            {
                'title': _lt('Procurement Analytics & Dashboards'),
                'description': _lt('Track KPIs like purchase trends, vendor performance, and lead times through tailored dashboards.'),
                'image': '/dekad_website/static/src/img/migrated/apps/purchase/image_9.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('End-to-End Procurement in One Platform'),
                    'description': _lt('From requisition to vendor payment, every step is automated and centralized within your ERP—no silos.')
                },
                {
                    'icon': 'fa-money',
                    'title': _lt('Cost Control & Compliance'),
                    'description': _lt('With three-way matching and blanket order support, you control costs, ensure accuracy, and maintain audit-ready records.')
                },
                {
                    'icon': 'fa-random',
                    'title': _lt('Smarter Vendor Negotiations'),
                    'description': _lt('Use vendor-specific pricelists, comparative RFQs, and performance stats to negotiate better deals.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Complex Operations'),
                    'description': _lt('Support multi-company procurement, multiple currencies, and hierarchical stock locations effortlessly.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Connected to Inventory & Finance'),
                    'description': _lt('Our Purchase module integrates with Inventory, Accounting, Manufacturing, and eCommerce—ensuring full visibility and synchronization.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Pro-Level Deployment by Dekad'),
                    'description': _lt('We set up templates, approval workflows, integrations, and provide training to maximize ROI from day one.')
                }
            ]
        }
    },
    'project': {
        'slug': 'project',
        'name': _lt('Project'),
        'subtitle': _lt('Streamline task assignment, track timelines and budgets, and keep all resources and communications in one centralized dashboard.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/project/cover_bg.webp',
        'overview': {
            'title': _lt('Smarter project management from planning to delivery'),
            'paragraphs': [
                _lt('At Dekad Software Solutions, our Project module enables teams to collaborate efficiently—handling everything from task scheduling and time tracking to profitability analysis and document sharing.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/project/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Visual Task Management'),
                'description': _lt('Use Kanban, list, and Gantt views to organize tasks, plan projects, and manage dependencies easily.'),
                'image': '/dekad_website/static/src/img/migrated/apps/project/image_2.png'
            },
            {
                'title': _lt('Time & Cost Tracking'),
                'description': _lt('Log time directly on tasks, compare expected vs. actual hours, and create invoices from billable time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/project/image_3.png'
            },
            {
                'title': _lt('Budget Insights & Burndown Charts'),
                'description': _lt('Monitor profitability with budget vs actual reporting and track project progress visually.'),
                'image': '/dekad_website/static/src/img/migrated/apps/project/image_4.png'
            },
            {
                'title': _lt('Integration with Sales & Invoicing'),
                'description': _lt('Convert projects into sales orders, automate billing, and manage milestones directly from Odoo.'),
                'image': '/dekad_website/static/src/img/migrated/apps/project/image_5.png'
            },
            {
                'title': _lt('Built-In Communication & Collaboration'),
                'description': _lt('Centralize discussions, documents, and task updates in each project workspace for streamlined teamwork.'),
                'image': '/dekad_website/static/src/img/migrated/apps/project/image_6.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Unified ERP Collaboration'),
                    'description': _lt('Projects, sales, timesheets, and accounting all tied together—no exports, no silos.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Visual & Real-Time Planning'),
                    'description': _lt('Easy-to-use planning tools help teams stay aligned and on schedule.')
                },
                {
                    'icon': 'fa-eye',
                    'title': _lt('Performance-Driven Projects'),
                    'description': _lt('With live cost tracking and reports, you stay in control of budgets and deadlines.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Seamless Scaling'),
                    'description': _lt('Adaptable for one project or many—with multiple teams and workflows.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Partner-Level Deployment'),
                    'description': _lt('Dekad configures templates, reporting, resource allocation, and trains your team for success.')
                }
            ]
        }
    },
    'field-service': {
        'slug': 'field-service',
        'name': _lt('Field Service'),
        'subtitle': _lt('Plan, execute, and invoice field tasks with real-time visibility and seamless ERP integration.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/field-service/cover_bg.webp',
        'overview': {
            'title': _lt('On-site operations — streamlined, tracked, and professional'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Field Service module empowers businesses to manage on-site work efficiently—from planning dispatch to capturing timesheets, parts used, and customer approval—all within one mobile-ready platform.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/field-service/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Multi-View Scheduling & Planning'),
                'description': _lt('Coordinate work using Kanban, Calendar, Gantt, Map, List, and Activity views—ideal for avoiding double-booking.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_2.png'
            },
            {
                'title': _lt('Mobile App with Offline Support'),
                'description': _lt('Allow technicians to work on-site regardless of internet access—fill worksheets, log hours, and get client signatures easily.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_3.webp'
            },
            {
                'title': _lt('Automated Task Generation'),
                'description': _lt('Create tasks from emails, web forms, sales orders, or helpdesk tickets—ensuring no client request goes unnoticed.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_4.png'
            },
            {
                'title': _lt('Integrated Timesheets & Reporting'),
                'description': _lt('Log time directly from each task, view time logs in Chatter, and analyze performance with pivot tables and charts.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_5.webp'
            },
            {
                'title': _lt('On-Site Invoicing & Inventory Updates'),
                'description': _lt('Generate quotations or invoices linked to tasks, send to clients on the spot, and deduct parts used from stock automatically.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_6.png'
            },
            {
                'title': _lt('Custom Task Worksheets & Client Feedback'),
                'description': _lt('Append pre-built worksheets, record materials and labor, collect client signatures, and provide service reports—all from the field.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_7.png'
            },
            {
                'title': _lt('Real-Time Analytics & Customer Ratings'),
                'description': _lt('Track operational KPIs like task completion, revenue, satisfaction scores, and service history for each customer.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_8.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All-in-One ERP Integration'),
                    'description': _lt('Field tasks tie directly into your Sales, Inventory, Accounting, and Helpdesk modules—no manual handoffs needed.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Boost Productivity & Accuracy'),
                    'description': _lt('Unified mobile workflows reduce data complexity and enable quick, accurate on-site service fulfillment.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Enhance Customer Experience'),
                    'description': _lt('With real-time scheduling, on-site invoicing, and digital sign-offs, clients enjoy smoother, transparent service.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Optimize Resource Planning'),
                    'description': _lt('Multi-view scheduling and activity logs empower better resource and technician allocation.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable & Secure'),
                    'description': _lt('Designed for growing mobile teams working across locations—supported by role-based access and audit trails.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Support from Dekad'),
                    'description': _lt('We handle setup, integrations, worksheet design, and training – ensuring your service teams hit the ground running.')
                }
            ]
        }
    },
    'timesheet': {
        'slug': 'timesheet',
        'name': _lt('Timesheet'),
        'subtitle': _lt('Record work effortlessly with timers or manual entry, and link hours to tasks, projects, or clients.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/timesheet/cover_bg.webp',
        'overview': {
            'title': _lt('Accurate time logging for better productivity and profitability'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Timesheet module ensures your teams log time consistently—delivering true labor tracking, payroll precision, and transparent client billing.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Start/Stop Timer & Flexible Entry'),
                'description': _lt('Record hours via a mobile-friendly timer or manually, with support for hours, minutes, days, or half-days.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_2.png'
            },
            {
                'title': _lt('Grid, Kanban & Analytics Views'),
                'description': _lt('View entries in grid, list, Kanban, pivot, or chart formats for team oversight and validation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_3.webp'
            },
            {
                'title': _lt('Overtime & Variance Tracking'),
                'description': _lt('Identify overtime, missing logs, and allocated vs actual hours at a glance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_4.png'
            },
            {
                'title': _lt('Approval Workflow & Reminders'),
                'description': _lt('Managers can review and validate entries, with reminders automating compliance.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_5.png'
            },
            {
                'title': _lt('Timesheet-Based Billing'),
                'description': _lt('Link hours to clients or projects and generate invoices directly from validated entries.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_6.png'
            },
            {
                'title': _lt('Access Control & Lock Dates'),
                'description': _lt('Set visibility rules, restrict editing past times, and secure data integrity.'),
                'image': '/dekad_website/static/src/img/migrated/apps/timesheet/image_7.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Built into Your ERP Experience'),
                    'description': _lt('Timesheets connect seamlessly with Projects, HR, Payroll, and Invoicing.')
                },
                {
                    'icon': 'fa-tasks',
                    'title': _lt('Boost Accountability & Accuracy'),
                    'description': _lt('Timers and reminder workflows ensure no hour goes unlogged or unbilled.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Insightful Time Analytics'),
                    'description': _lt('Use real-time dashboards to monitor productivity, project progress, and resource allocation.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Teams & Clients'),
                    'description': _lt('Work across internal teams or client-based projects—across locations and currencies.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Efficient Deployment by Dekad'),
                    'description': _lt('We assist with rules, templates, automated reminders, and training for smooth adoption and reporting accuracy.')
                }
            ]
        }
    },
    'appointments': {
        'slug': 'appointments',
        'name': _lt('Appointments'),
        'subtitle': _lt('Allow customers to book meetings, consultations, or service appointments online—anytime and on any device. Let them view availability, select time slots, and receive instant confirmations and reminders.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/appointments/cover_bg.webp',
        'overview': {
            'title': _lt('Self-service appointment scheduling that works in your favor'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Appointments module empowers businesses to streamline client bookings and optimize schedules across teams and resources. With integrated calendars, video conferencing, and analytics, self-service scheduling becomes effortless and efficient.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/appointments/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Multiple booking types (individual/team/resource)'),
                'description': _lt('Publish personal, team-wide, or resource-specific appointment pages suited to different needs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_2.webp'
            },
            {
                'title': _lt('Calendar integration & no double-booking'),
                'description': _lt('Connect to Odoo, Google, or Outlook calendars. Real-time sync prevents scheduling conflicts.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_3.webp'
            },
            {
                'title': _lt('Automated reminders & confirmations'),
                'description': _lt('Send customizable email/SMS reminders and confirmation or cancellation alerts—reducing no-shows.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_4.webp'
            },
            {
                'title': _lt('Pre-booking rules & buffer times'),
                'description': _lt('Set minimal lead times, padding between appointments, time zones, and cancellation policies.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_5.webp'
            },
            {
                'title': _lt('Integrated CRM & Opportunities'),
                'description': _lt('Automatically convert bookings into leads or opportunities for immediate sales follow-up.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_6.png'
            },
            {
                'title': _lt('Custom forms & guest invitations'),
                'description': _lt('Add booking questions during scheduling and allow guests to join appointments by invitation.'),
                'image': '/dekad_website/static/src/img/migrated/apps/field-service/image_7.png'
            },
            {
                'title': _lt('Reporting & analytics dashboard'),
                'description': _lt('View appointment statistics—booking rates, resource demand, no-shows—through clear reporting tools.'),
                'image': '/dekad_website/static/src/img/migrated/apps/appointments/image_7.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Made for Your Team & Clients'),
                    'description': _lt('Self-service booking reduces friction and workload. You set the rules—clients pick a slot.')
                },
                {
                    'icon': 'fa-calendar',
                    'title': _lt('Synchronised Scheduling Everywhere'),
                    'description': _lt("With calendar integration, your team's availability is always current and conflict-free.")
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Professional & Automated'),
                    'description': _lt('Confirmation messages, reminders, and rescheduling at scale—without lifting a finger.')
                },
                {
                    'icon': 'fa-cubes',
                    'title': _lt('Optimise Your Resources'),
                    'description': _lt('Assign and manage meetings across people or assets effortlessly—avoid overlapping or underuse.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Actionable Insights'),
                    'description': _lt('With reporting on client behavior and appointment trends, you make smarter resource decisions.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Supportive Implementation by Dekad'),
                    'description': _lt('We set up booking types, calendar sync, communication templates, reporting dashboards, and user training to ensure smooth rollout.')
                }
            ]
        }
    },
    'events': {
        'slug': 'events',
        'name': _lt('Event Management'),
        'subtitle': _lt('Organize in-person or online events with built-in agendas, tickets, registrations, booths, and attendee tracking—all mapped seamlessly into your ERP.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/events/cover_bg.webp',
        'overview': {
            'title': _lt('Powerful event management—from creation to attendee engagement'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Events module enables you to manage every aspect of an event—it handles event creation, ticketing, promotions, scheduling, and follow-up. With intelligent dashboards and real-time analytics, you gain full visibility and control over attendee experience, revenue, and event logistics.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/events/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Drag-and-Drop Event Builder'),
                'description': _lt('Effortlessly create landing pages, schedules, tracks, speaker bios, and calls to action—using visual building blocks and themes.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_2.png'
            },
            {
                'title': _lt('Ticketing & Booth Sales'),
                'description': _lt('Set tiered pricing, limit registrations, sell tickets via website, and manage exhibitor booths with multi-level options.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_3.webp'
            },
            {
                'title': _lt('Registration Forms & Attendee Management'),
                'description': _lt('Customize registration questions, use QR/barcode check-in, and track attendee confirmations in real time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_4.png'
            },
            {
                'title': _lt('Tracks & Speaker Management'),
                'description': _lt('Create session tracks, accept speaker proposals, schedule talks, and enable live broadcasts or quizzes.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_5.png'
            },
            {
                'title': _lt('Automated Communications & Promotion'),
                'description': _lt('Launch email/SMS/social campaigns, schedule reminders, and integrate SEO, social hashtags, and analytics.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_6.webp'
            },
            {
                'title': _lt('On-Site Check-In Desk'),
                'description': _lt('Use a registration desk interface with badge printing and QR scanning to streamline event access.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_7.png'
            },
            {
                'title': _lt('Comprehensive Analytics & Reporting'),
                'description': _lt('Monitor revenue, attendee metrics, sources, lead generation, satisfaction surveys, and booth performance via dashboards.'),
                'image': '/dekad_website/static/src/img/migrated/apps/events/image_8.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Seamless ERP Integration'),
                    'description': _lt('From event creation to finances, tickets, and marketing, everything flows through your unified Odoo system.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Reduce Manual Overhead'),
                    'description': _lt('Templates, automated communications, and integrated ticketing make event setup fast and efficient.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Boost Engagement & Leads'),
                    'description': _lt('Smart promotions, live check-in, and workshops convert attendees into leads and customers.')
                },
                {
                    'icon': 'fa-lightbulb-o',
                    'title': _lt('Professional Experience Everywhere'),
                    'description': _lt('Give attendees confidence with branded websites, QR badges, slick agendas, and follow-up messaging.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Scalable for Any Event'),
                    'description': _lt('From workshops to large conferences—events of various types and sizes can be managed with ease.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Setup by Dekad'),
                    'description': _lt('We implement your event templates, booking flows, communication triggers, registration setup, and analytics dashboards for optimal results.')
                }
            ]
        }
    },
    'discuss': {
        'slug': 'discuss',
        'name': _lt('Discuss'),
        'subtitle': _lt('Centralize internal messaging, group channels, notifications, voice/video calls, and WhatsApp—all within Odoo’s unified interface.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/discuss/cover_bg.webp',
        'overview': {
            'title': _lt('Unified team communication within your ERP'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Discuss module streamlines your communication infrastructure by integrating real-time chat and media-rich collaboration directly with all your business apps. No more switching between tools—stay connected, informed, and efficient.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/discuss/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Private & Group Conversations'),
                'description': _lt('One-on-one chats and team channels with threaded replies, reactions, starring, and history views.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_2.webp'
            },
            {
                'title': _lt('Voice & Video Calls'),
                'description': _lt('Start voice or video meetings—including screen sharing and hand-raise functionality—right from chat or calendar invites.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_3.webp'
            },
            {
                'title': _lt('WhatsApp & Email Notifications'),
                'description': _lt('Engage over WhatsApp and capture email alerts in the same app inbox for convenient, consolidated messaging.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_4.webp'
            },
            {
                'title': _lt('Chatter Integration Across All Apps'),
                'description': _lt('Every document in Odoo (e.g., sales orders, projects) includes chatter connected directly to Discuss—ensuring context-rich cross-app visibility.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_5.webp'
            },
            {
                'title': _lt('Channel-Based Announcements'),
                'description': _lt('Broadcast updates to teams using designated channels for focused communication and automatic follower subscription.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_6.webp'
            },
            {
                'title': _lt('Rich Interactions & Media Support'),
                'description': _lt('React with emojis/GIFs, pin important posts, preview links, and search conversations quickly for just-in-time insight.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_7.webp'
            },
            {
                'title': _lt('Inbox & Activity Stream'),
                'description': _lt('View unread messages, starred items, and history in one combined inbox—without switching tabs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/discuss/image_4.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('One Communication Platform'),
                    'description': _lt('Say goodbye to fragmented tools. Discuss unifies chat, calls, and notifications—without leaving Odoo.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Embedded in Workflows'),
                    'description': _lt('Discuss is accessible from anywhere in your ERP—on orders, projects, or records—preserving full context.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Secured & Audit-Ready'),
                    'description': _lt('All conversations and actions are logged, manageable via permissions and audit trails—ensuring compliance.')
                },
                {
                    'icon': 'fa-lightbulb-o',
                    'title': _lt('Enhance Team Productivity'),
                    'description': _lt('Real-time chat, workflows, broadcasting, and visibility all improve responsiveness and collaboration.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Efficient Internal Connect'),
                    'description': _lt('Reduce inbox clutter, streamline communication, and increase engagement across your organization.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Deployment & Training by Dekad'),
                    'description': _lt('We set up channels, integrate communication flows, configure access levels, and train your team to ensure seamless adoption.')
                }
            ]
        }
    },
    'approvals': {
        'slug': 'approvals',
        'name': _lt('Approvals'),
        'subtitle': _lt('Streamline all types of internal requests—travel, expenditures, purchases, contracts—through a unified approval interface. Customize approver roles, request types, and stages effortlessly.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/approvals/cover_bg.webp',
        'overview': {
            'title': _lt('Centralized digital approvals for efficient workflow'),
            'paragraphs': [
                _lt('At Dekad Software Solutions, our Approvals module simplifies decision-making across your organization. Users submit requests via customizable forms, and designated approvers respond in a single, traceable dashboard—removing email chains and accelerating response times.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/approvals/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Custom Approval Types & Form Builder'),
                'description': _lt('Create request types tailored to your process (e.g., business trips or hardware purchases), using configurable forms to gather the required information.'),
                'image': '/dekad_website/static/src/img/migrated/apps/approvals/image_2.png'
            },
            {
                'title': _lt('Configurable Multi-Level Workflows'),
                'description': _lt('Define multiple approvers—mandatory or optional—and set approval sequences, using Studio if needed for embedded rules.'),
                'image': '/dekad_website/static/src/img/migrated/apps/approvals/image_3.png'
            },
            {
                'title': _lt('Central Dashboard & Color-Coded Status'),
                'description': _lt('Track all requests at a glance with a unified dashboard; color-coded request stages highlight pending, approved, or refused items.'),
                'image': '/dekad_website/static/src/img/migrated/apps/approvals/image_4.png'
            },
            {
                'title': _lt('Chatter Integration & Comments'),
                'description': _lt('Collaborate securely on approvals via built-in messaging—add notes, attach documents, and communicate before finalizing decisions.'),
                'image': '/dekad_website/static/src/img/migrated/apps/approvals/image_5.png'
            },
            {
                'title': _lt('Attachments & Validation'),
                'description': _lt('Upload supporting documents (bills, contracts, quotes) at submission or later stages and maintain full context with record logs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/approvals/image_6.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Unified Request Management'),
                    'description': _lt('Handle all internal approvals within Odoo—no disjointed platforms or siloed email workflows.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Faster & Transparent Decisions'),
                    'description': _lt('Visual queues, sequence controls, and prompt reminders keep requests moving efficiently.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Flexible to Fit Your Policies'),
                    'description': _lt('Whether simple (one approver) or complex (multi-tier), workflows adapt effortlessly to your needs.')
                },
                {
                    'icon': 'fa-lightbulb-o',
                    'title': _lt('Clear Traceability & Audit Trails'),
                    'description': _lt('Chatter logs, comment history, and approval timelines ensure full compliance and transparency.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Extendable Beyond HR'),
                    'description': _lt('Apply approvals to any business area—expenses, inventory transfers, sales discounts, project budgets.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Configuration By Dekad'),
                    'description': _lt('We’ll design form types, approval pipelines, integration with modules (Expense, Purchase, Project, etc.), and train your team for seamless uptake.')
                }
            ]
        }
    },
    'e-signatures': {
        'slug': 'e-signatures',
        'name': _lt('E-Signatures'),
        'subtitle': _lt('Send, sign, and approve documents digitally from any device. Keep full audit trails, authentication, and regulatory compliance within a single unified platform.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/sign/cover_bg.webp',
        'overview': {
            'title': _lt('Secure, legal, and seamless e-signatures—anytime, anywhere'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, we simplify how you handle contracts, approvals, and employee documents with Odoo Sign. Built-in workflows and cryptographic logging replace manual processes with speed, security, and professionalism.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/sign/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Custom Signature Input'),
                'description': _lt('Allow users to sign via handwritten fonts, drawing, or uploading a scanned signature.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_2.webp'
            },
            {
                'title': _lt('Drag & Drop Templates'),
                'description': _lt('Build reusable documents by placing fields, mandatory or optional, into PDFs—automating repetitive signatures.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_3.webp'
            },
            {
                'title': _lt('Signing Order & Multi-Role Support'),
                'description': _lt('Set the sequence of signers and assign distinct roles—ensuring controlled, role-based workflows.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_4.jpg'
            },
            {
                'title': _lt('Secure Authentication & Traceability'),
                'description': _lt('Authenticate signers via SMS or itsme®, capture IP address/time stamps, and embed cryptographic traces in audit logs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_5.jpg'
            },
            {
                'title': _lt('Automated Reminders & Delivery Control'),
                'description': _lt('Schedule automatic reminders, track progress, and send completed documents or CCs to designated recipients.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sign/image_6.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Complete ERP Integration'),
                    'description': _lt('Signature workflows embed directly within Sales, HR, Accounting, Recruitment, Rental, and Field Service modules—no extra apps needed.')
                },
                {
                    'icon': 'fa-arrow-down',
                    'title': _lt('Error-Free, Traceable Process'),
                    'description': _lt('Role-based fields, digital logs, and secure validation ensure each document is accurate, auditable, and legally binding.')
                },
                {
                    'icon': 'fa-flash',
                    'title': _lt('Instant, Automated Workflow'),
                    'description': _lt('With reusable templates, reminders, and CC settings, you’ll reduce turnaround time and eliminate manual follow-up.')
                },
                {
                    'icon': 'fa-lightbulb-o',
                    'title': _lt('Universal Device Support'),
                    'description': _lt('Clients, employees, and partners can sign from any browser or mobile device—anywhere, any time.')
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Proven Security Framework'),
                    'description': _lt('Encrypted storage, SMS authentication, IP logging, and cryptographic seals keep your documents secure and trusted.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Expert Implementation & Support'),
                    'description': _lt('Dekad sets up your templates, authorization flows, security options, and trains your team for confident, compliant adoption.')
                }
            ]
        }
    },
    'documents': {
        'slug': 'documents',
        'name': _lt('Documents'),
        'subtitle': _lt('Store, preview, share, and automate your documents—all within one unified platform. Categorize by workspace, tag files, and control access for optimal organization.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/documents/cover_bg.webp',
        'overview': {
            'title': _lt('Centralized, collaborative, and smart document management'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, the Documents module eliminates paper chaos. It provides a streamlined digital hub for managing contracts, invoices, marketing assets, and HR files—backed by OCR automation and seamless ERP integration.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/documents/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Workspace Organization & Tagging'),
                'description': _lt('Group documents into dedicated workspaces—like company, personal, or shared—and apply custom tags for quick retrieval.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_2.png',
            },
            {
                'title': _lt('Preview & Chat Inside Documents'),
                'description': _lt('View PDFs, images, videos, spreadsheets inline. Use chatter to collaborate, assign tasks, or add notes without exporting.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_3.png',
            },
            {
                'title': _lt('Split, Merge & OCR Process'),
                'description': _lt('Split PDFs, merge files, and let AI extract data from invoices or bills to auto-create vendor/customer entries.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_4.png',
            },
            {
                'title': _lt('Digital Document Requests'),
                'description': _lt('Send “missing document” requests with reminders to teammates or clients—complete with deadlines and auto follow-ups.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_5.png',
            },
            {
                'title': _lt('Secure Sharing & Access Control'),
                'description': _lt('Share documents or folders with internal users or external guests—set roles, expiration dates, and permissions.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_6.webp',
            },
            {
                'title': _lt('Integration with 80+ Odoo Apps'),
                'description': _lt('Link docs to Sales, Purchase, HR, Projects, PLM, Sign, and more—ensuring files are contextually stored and traceable.'),
                'image': '/dekad_website/static/src/img/migrated/apps/documents/image_7.webp',
            },
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Erase File Friction'),
                    'description': _lt('Replace scattered docs, email attachments, and local folders with a unified, searchable document hub.'),
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Automated & Enhanced workflows'),
                    'description': _lt('OCR, automated processing, and reminders reduce manual tasks, streamline approvals, and free up time.'),
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Collaborate Securely'),
                    'description': _lt('Shared workspaces, chat, and access controls empower teams to work together confidently and compliantly.'),
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Traceable & Regulatory-ready'),
                    'description': _lt('Audit-friendly version control, logs, and controlled sharing ensure compliance and data security.'),
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Grow without Limits'),
                    'description': _lt('From small shared folders to complex, multi-workspace setups, the solution scales as your business expands.'),
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Implementation Support by Dekad'),
                    'description': _lt('We configure spaces, access rules, integrations, automations, and train your team to maximize usage and compliance.'),
                },
            ],
        },
    },
    'calendar': {
        'slug': 'calendar',
        'name': _lt('Calendar'),
        'subtitle': _lt('Organize meetings, events, appraisal sessions, project tasks, and more within a centralized platform. Enjoy Day, Week, Month, and Year views with weekend display options and quick navigation tools.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/calendar/cover_bg.png',
        'overview': {
            'title': _lt('Your unified scheduling hub—integrated across the entire ERP'),
            'paragraphs': [
                _lt("At Dekad Software Solutions, our Calendar module transforms scheduling into an organized, collaborative process. With seamless integration into CRM, Projects, Helpdesk, and Attendance, you get unified visibility and control over your team’s time and resources.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/calendar/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Multi‑View Scheduling'),
                'description': _lt('Choose between Day, Week, Month, or Year views and toggle weekend display. Navigate quickly using today/next/previous controls.'),
                'image': '/dekad_website/static/src/img/migrated/apps/calendar/image_2.png'
            },
            {
                'title': _lt('Third‑Party Calendar Sync'),
                'description': _lt('Two‑way synchronization with Google and Outlook calendars ensures all events are updated across platforms.'),
                'image': '/dekad_website/static/src/img/migrated/apps/calendar/image_3.png'
            },
            {
                'title': _lt('Create Events from Within Odoo'),
                'description': _lt('Schedule directly from Chatter or records—link activities like meetings or calls to CRM, Projects, or other apps.'),
                'image': '/dekad_website/static/src/img/migrated/apps/calendar/image_4.png'
            },
            {
                'title': _lt('Advanced Event Options'),
                'description': _lt('Configure attendees, virtual meeting links, timezones, recurrence rules, reminders, tags, and privacy settings using an intuitive form.'),
                'image': '/dekad_website/static/src/img/migrated/apps/calendar/image_5.png'
            },
            {
                'title': _lt('Team Availability & Group Scheduling'),
                'description': _lt('Display team calendars side-by-side to identify free slots and avoid booking conflicts.'),
                'image': '/dekad_website/static/src/img/migrated/apps/calendar/image_5.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Centralized Scheduling, Unified View'),
                    'description': _lt('Everything—from project deadlines to customer calls—is on a single platform, ensuring visibility and avoiding fragmentation.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Sync with the Tools You Use'),
                    'description': _lt('Google and Outlook integration ensures no meetings are double booked or missed, no matter where they’re scheduled.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Contextual Meetings'),
                    'description': _lt('Create events directly from CRM leads or project tasks, ensuring appointments are aligned with business activities.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Flexible, Feature-Rich Planner'),
                    'description': _lt('With support for recurrence, reminders, virtual links, and privacy controls, scheduling adapts to diverse workflows.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Collaborative Efficiency'),
                    'description': _lt('Team calendar views and attendee scheduling improve coordination and reduce meeting conflicts.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Seamless Deployment by Dekad'),
                    'description': _lt('We integrate and configure calendar sync, activity flows, event templates, reminders, and provide training for efficient adoption.')
                }
            ]
        }
    },
    'website': {
        'slug': 'website',
        'name': _lt('Website Builder'),
        'subtitle': _lt('Everything is modular, mobile-ready, and seamlessly integrated. No technical background needed. Just drag, drop, and launch.'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/website/cover_bg.webp',
        'overview': {
            'title': _lt("Build beautiful, fully integrated websites—powered by Odoo's Website app"),
            'paragraphs': [
                _lt("With Odoo, you can build modern, responsive websites using a powerful visual editor. Whether you're creating landing pages, static content, or dynamic eCommerce and blog modules, Odoo’s Website module gives you full control—directly connected to other business applications like Sales, CRM, and Inventory.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/website/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Drag-and-Drop Page Builder'),
                'description': _lt('Create and customize pages using building blocks with real-time previews—no coding required.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_2.webp'
            },
            {
                'title': _lt('Theme-Based Design'),
                'description': _lt('Choose from professional themes with flexible layout options. Switch or customize themes at any time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_3.png'
            },
            {
                'title': _lt('Static & Dynamic Pages'),
                'description': _lt('Manage both static pages (About, Contact, etc.) and dynamic pages (eCommerce, Blog, Events) directly from the frontend or backend.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_4.png'
            },
            {
                'title': _lt('Page Management & Publishing'),
                'description': _lt('Duplicate, delete, and publish pages in one click. Schedule publication dates or unpublish as needed.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_5.png'
            },
            {
                'title': _lt('Menu & Navigation Control'),
                'description': _lt('Easily add pages to your website’s menu and manage URL paths and page visibility.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_6.webp'
            },
            {
                'title': _lt('SEO Optimization Tools'),
                'description': _lt('Access SEO tools to manage meta titles, descriptions, keywords, and image alt text. Real-time previews and optimization tips included.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_7.png'
            },
            {
                'title': _lt('Schema, Sitemaps & Robots'),
                'description': _lt('Supports schema.org for rich snippets and auto-generates robots.txt and sitemap.xml for optimal indexing.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_8.webp'
            },
            {
                'title': _lt('Auto WebP Conversion & Compression'),
                'description': _lt('Images are auto-converted to WebP and compressed for fast page loads. Add alt text and configure display settings directly in the editor.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_9.png'
            },
            {
                'title': _lt('Multi-Language & RTL Support'),
                'description': _lt('Build websites in multiple languages with automatic hreflang tags and full right-to-left layout compatibility for Arabic and similar scripts.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_10.webp'
            },
            {
                'title': _lt('Domain & SSL Management'),
                'description': _lt('Configure domain names, SSL certificates, and DNS records from the backend. Odoo Online offers a free one-year domain.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_11.png'
            },
            {
                'title': _lt('Multi-Website Support'),
                'description': _lt('Run multiple websites from a single database. Each can have its own domain, language, theme, and content.'),
                'image': '/dekad_website/static/src/img/migrated/apps/website/image_12.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Easy Setup'),
                    'description': _lt('Get started in minutes using page templates like Landing, About, Services, and Gallery—all customizable from the frontend.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Business Integration'),
                    'description': _lt('Fully integrated with Odoo Sales, CRM, Events, eCommerce, and more. No need for external plugins.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('SEO Built-In'),
                    'description': _lt('From alt text to meta titles, Odoo helps you build search-engine friendly content right from the page editor.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Centralized Page Control'),
                    'description': _lt('Manage URLs, publishing rules, page access levels (public, logged-in, or password-protected), and redirects—all in one place.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Automatic Sitemap & Robots.txt'),
                    'description': _lt('Ensure your site is indexed correctly with auto-generated sitemap and robots files—updated every 12 hours.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Mobile-Responsive Design'),
                    'description': _lt('All pages and blocks are fully responsive, ensuring seamless experience across devices.')
                }
            ]
        }
    },
    'ecommerce': {
        'slug': 'ecommerce',
        'name': _lt('eCommerce'),
        'subtitle': _lt('Create, manage, and grow your online store—all from a single, powerful platform'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/ecommerce/cover_bg.webp',
        'overview': {
            'title': _lt('Everything is modular, mobile-optimized, and fully connected—no coding required. Just choose, customize, and go live.'),
            'paragraphs': [
                _lt("Build a fully functional online shop that works seamlessly with your product catalog, inventory, and customer experience. Whether you're selling physical products, digital files, or a mix of both, the system provides everything you need to get started and scale."),
                _lt("Design beautiful product pages, manage variants and stock in real time, and offer flexible delivery methods—all while delivering a smooth and engaging shopping experience for your customers.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Product Catalog Management'),
                'description': _lt('Organize your shop with categories, filters, and variants. Add products directly from the frontend or backend, or import them in bulk using spreadsheets. Support for digital products and multi-language fields is included.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_2.png'
            },
            {
                'title': _lt('Shop and Category Pages'),
                'description': _lt('Offer customers an intuitive browsing experience with customizable layouts, filters (by price, attributes, categories), sorting options, and product badges like “New” or “On Sale.”'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_3.png'
            },
            {
                'title': _lt('Customizable Product Pages'),
                'description': _lt('Build visually appealing product pages with image galleries, video support, carousels, zoom effects, and customer reviews. Add wishlist and comparison buttons, display tax details, and allow quantity selection.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_4.webp'
            },
            {
                'title': _lt('Variants and Comparison Tools'),
                'description': _lt('Define product attributes like size or color to generate variants. Enable comparison tools so customers can evaluate products based on key features and specifications.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_5.webp'
            },
            {
                'title': _lt('Digital Downloads'),
                'description': _lt('Attach downloadable files to product pages—such as manuals or certificates—and control access either before or after purchase, with files available in the customer portal.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_6.webp'
            },
            {
                'title': _lt('Multi-Language and Multi-Website Support'),
                'description': _lt('Translate product information and set availability per website. Manage multiple storefronts, each with its own catalog, language, and design—managed from one central location.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_7.png'
            },
            {
                'title': _lt('Inventory and Stock Control'),
                'description': _lt('Choose how stock is managed across warehouses. Decide if out-of-stock items can still be sold, and show real-time stock availability to customers.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_8.webp'
            },
            {
                'title': _lt('Delivery and Shipping Options'),
                'description': _lt('Configure delivery methods and connect with popular shipping providers. Allow customers to select their preferred shipping option at checkout.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_9.webp'
            },
            {
                'title': _lt('Customer Portal'),
                'description': _lt('Give your customers a personalized dashboard where they can track their orders, download purchased files, view invoices, and manage their profile—offering transparency and convenience.'),
                'image': '/dekad_website/static/src/img/migrated/apps/ecommerce/image_10.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All-in-One eCommerce Management'),
                    'description': _lt('Run your store, manage inventory, process orders, and handle payments in one place—without relying on disconnected third-party systems.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Full Control from Frontend or Backend'),
                    'description': _lt('Create and edit products, categories, and content from either the public website or the admin dashboard—whichever fits your workflow.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Enhanced Shopping Experience'),
                    'description': _lt('Give your customers advanced filtering, smooth navigation, responsive design, and convenient tools like wishlists and comparisons.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Support for Digital Products'),
                    'description': _lt('Easily sell downloadable goods and manage customer access, ideal for e-books, manuals, certificates, or gated files.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Flexible Stock and Delivery Settings'),
                    'description': _lt('Decide how inventory is displayed and managed. Enable backorders, configure warehouse rules, and offer diverse shipping options.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Multi-Site & Language Ready'),
                    'description': _lt('Expand to new regions with localized storefronts and content—customized per market, but all managed from a single system.')
                }
            ]
        }
    },
    'blog-forum': {
        'slug': 'blog-forum',
        'name': _lt('Blog & Forum'),
        'subtitle': _lt('Engage your audience and foster a community—right within your website'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/blog-forum/cover_bg.png',
        'overview': {
            'title': _lt('Everything is modular, mobile-optimized, and easy to manage—no technical complexity. Just design your content, customize layouts, and go live.'),
            'paragraphs': [
                _lt("Launch both a fully-featured blog and interactive forum without needing external tools. The blog module lets you craft and publish articles with tags, sidebars, and customizable layouts. Meanwhile, the forum module offers a question-and-answer space with moderation, karma points, badges, and ranks to motivate contribution and nurture a vibrant user community")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Blog Creation & Management'),
                'description': _lt('Set up multiple blogs (e.g., Latest News, Tutorials) with configurable names and subtitles. Posts are added via a simple “+New → Blog Post” workflow and instantly integrated into your site’s navigation'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_2.webp'
            },
            {
                'title': _lt('Rich Blog Post Layouts'),
                'description': _lt('Customize post templates using building blocks. Choose grid or list layouts, include banners, adjust sidebar content (archives, tags, “About Us,” social links), and arrange post metadata and format using editing tools'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_3.png'
            },
            {
                'title': _lt('Tag-Based Filtering'),
                'description': _lt('Enable tags for each post—readers can filter content by theme. Tags and tag categories are manageable through backend configuration and can be added directly during editing'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_4.png'
            },
            {
                'title': _lt('Customizable Blog Homepage'),
                'description': _lt('Design blog landing pages with flexible layout options: top-banner modes, grid/list view, card effects, readability settings, and sidebar components like archives, tags, and “Follow Us” widgets'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_5.png'
            },
            {
                'title': _lt('Forum Setup & Moderation'),
                'description': _lt('Create forums configured for either Q&A or open discussions. Set default sorting (Newest, Most Voted, etc.), privacy levels (Public, Signed In, or restricted groups), and enable moderation tools'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_6.webp'
            },
            {
                'title': _lt('Karma Points & Gamification'),
                'description': _lt('Users earn or lose karma through posting, voting, answering, accepting, flagging content. Tiers unlock privileges, which are configurable per forum. Ranks and badges can be defined manually or awarded based on karma or completed challenges'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_7.webp'
            },
            {
                'title': _lt('Tags in Forum'),
                'description': _lt('Allow users to tag posts and filter forum threads. Tags can be managed via backend, and permissions depend on karma levels'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_8.png'
            },
            {
                'title': _lt('Interactive Q&A Platform'),
                'description': _lt('Users can post questions, answer, comment, upvote/downvote, mark answers as best, favorite, follow, share social links, and flag offensive content—all with intuitive UI controls'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_9.png'
            },
            {
                'title': _lt('Complete Moderation Tools'),
                'description': _lt('Front-end moderation panels provide access to pending validations, flagged posts, closed threads, and post actions like close/reopen/delete. Admins can configure close reasons and handle exports or archives'),
                'image': '/dekad_website/static/src/img/migrated/apps/blog-forum/image_10.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Unified Content & Community'),
                    'description': _lt('Host both blog and forum features within the same platform—no need for third-party integrations. Seamlessly manage content and community from a single admin area.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Customizable & Scalable'),
                    'description': _lt('Adjust layouts, sidebars, and content flow for both blogs and forums to match your brand. Add multiple blogs or forums tailored to audience segments or subjects.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Engaged Communities Through Gamification'),
                    'description': _lt('Motivate users with a points system, ranks, badges, and karma-based rewards that encourage meaningful contributions and self-moderation.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Full Access Control'),
                    'description': _lt('Manage who sees what—set privacy tiers for forums, moderate content flows, and decide what appears on the frontend.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Content Discoverability & Filtering'),
                    'description': _lt('Use tags, archives, and post filters across both modules to help readers find relevant information quickly.')
                },
                {
                    'icon': 'fa-thumbs-o-up',
                    'title': _lt('Responsive & User-Friendly'),
                    'description': _lt('Both blog posts and forum threads feature mobile-optimized layouts with NO coding required—just easy content editing and publishing tools.')
                }
            ]
        }
    },
    'live-chat': {
        'slug': 'live-chat',
        'name': _lt('Live Chat'),
        'subtitle': _lt('Start the conversation—right when it matters most'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/live-chat/cover_bg.png',
        'overview': {
            'title': _lt('Set it up fast, customize the chat, and start real conversations—without any complexity.'),
            'paragraphs': [
                _lt('Live Chat empowers your team to interact with website visitors in real time—whether they’re browsing products, seeking support, or ready to make a decision. It bridges the gap between interest and action, offering a frictionless way to answer questions, provide assistance, and capture leads on the spot.')
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Real-Time Website Chat'),
                'description': _lt('Visitors can start chatting instantly from any page of your website using a sleek, embedded widget.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_2.png',
            },
            {
                'title': _lt('Quick Installation'),
                'description': _lt('Install the app, enable it through Helpdesk or Website settings, and start chatting—no technical setup required.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_3.png',
            },
            {
                'title': _lt('Custom Live Chat Channels'),
                'description': _lt('Create separate channels for different teams or purposes—like sales, support, or inquiries—each with unique configurations.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_4.png',
            },
            {
                'title': _lt('Operator Management'),
                'description': _lt('Assign team members as operators to respond to messages live. Modify availability and responsibilities anytime.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_5.png',
            },
            {
                'title': _lt('Fully Customizable Widget'),
                'description': _lt('Edit the button design, welcome message, and notification text to match your brand’s tone and visual identity.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_6.png',
            },
            {
                'title': _lt('Smart Display Rules'),
                'description': _lt('Define how and where the chat appears—by country, page URL, or timing. Set triggers like automatic pop-up after a delay.'),
                'image': '/dekad_website/static/src/img/migrated/apps/live-chat/image_7.png',
            },
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-comments',
                    'title': _lt('Talk to Visitors, Instantly'),
                    'description': _lt('Host both blog and forum features within the same platform—no need for third-party integrations. Seamlessly manage content and community from a single admin area.'),
                },
                {
                    'icon': 'fa-arrows-alt',
                    'title': _lt('Tailored to Your Business'),
                    'description': _lt('Adjust layouts, sidebars, and content flow for both blogs and forums to match your brand. Add multiple blogs or forums tailored to audience segments or subjects.'),
                },
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Always in the Right Place'),
                    'description': _lt('Motivate users with a points system, ranks, badges, and karma-based rewards that encourage meaningful contributions and self-moderation.'),
                },
                {
                    'icon': 'fa-expand',
                    'title': _lt('Simple to Launch, Easy to Scale'),
                    'description': _lt('Manage who sees what—set privacy tiers for forums, moderate content flows, and decide what appears on the frontend.'),
                },
            ],
        },
    },
    'elearning': {
        'slug': 'elearning',
        'name': _lt('eLearning'),
        'subtitle': _lt('Transform learning and discussion into one seamless experience'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/elearning/cover_bg.webp',
        'overview': {
            'title': _lt('Everything is modular, visually appealing, and easy to manage—no technical setup needed. Just create, customize, and launch.'),
            'paragraphs': [
                _lt("Build engaging online courses with rich content, assessments, certifications, and a built-in discussion forum—all from an intuitive, unified interface. Whether you're training employees, educating customers, or certifying users, your content, community, and analytics live under one roof.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/elearning/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Course & Content Management'),
                'description': _lt('Set up multiple blogs (e.g., Latest News, Tutorials) with configurable names and subtitles. Posts are added via a simple “+New → Blog Post” workflow and instantly integrated into your site’s navigation'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_2.png'
            },
            {
                'title': _lt('Assessments & Quizzes'),
                'description': _lt('Customize post templates using building blocks. Choose grid or list layouts, include banners, adjust sidebar content (archives, tags, “About Us,” social links), and arrange post metadata and format using editing tools'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_3.png'
            },
            {
                'title': _lt('Certifications & Badges'),
                'description': _lt('Enable tags for each post—readers can filter content by theme. Tags and tag categories are manageable through backend configuration and can be added directly during editing'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_4.webp'
            },
            {
                'title': _lt('Karma, Achievements & Leaderboards'),
                'description': _lt('Design blog landing pages with flexible layout options: top-banner modes, grid/list view, card effects, readability settings, and sidebar components like archives, tags, and “Follow Us” widgets'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_5.png'
            },
            {
                'title': _lt('Customer Portal'),
                'description': _lt('Create forums configured for either Q&A or open discussions. Set default sorting (Newest, Most Voted, etc.), privacy levels (Public, Signed In, or restricted groups), and enable moderation tools'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_6.webp'
            },
            {
                'title': _lt('Built‑In Forum'),
                'description': _lt('Users earn or lose karma through posting, voting, answering, accepting, flagging content. Tiers unlock privileges, which are configurable per forum. Ranks and badges can be defined manually or awarded based on karma or completed challenges'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_7.png'
            },
            {
                'title': _lt('Course Configuration & Enrollment'),
                'description': _lt('Allow users to tag posts and filter forum threads. Tags can be managed via backend, and permissions depend on karma levels'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_8.png'
            },
            {
                'title': _lt('Reporting & Analytics'),
                'description': _lt('Users can post questions, answer, comment, upvote/downvote, mark answers as best, favorite, follow, share social links, and flag offensive content—all with intuitive UI controls'),
                'image': '/dekad_website/static/src/img/migrated/apps/elearning/image_9.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All‑in‑One Learning Platform'),
                    'description': _lt('Content, assessments, discussion forums, certificates, and analytics—no plugins or integrations needed.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Content and Community in One Place'),
                    'description': _lt('Courses and forums coexist, making learning interactive and supported by collaboration.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Gamification to Boost Engagement'),
                    'description': _lt('Points, badges, and leaderboards encourage participation and continuous learning.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Flexible Enrollment Options'),
                    'description': _lt('Choose between free, invite-only, or paid courses—sell access directly through configurable enrollment options.')
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Data‑Driven Insights'),
                    'description': _lt('Track performance across multiple dimensions (views, reviews, revenue, quiz results) for better course management.')
                }
            ]
        }
    },
    'social-media-marketing': {
        'slug': 'social-media-marketing',
        'name': _lt('Social Media Marketing'),
        'subtitle': _lt('Tap into the social revolution—where billions connect'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/cover_bg.webp',
        'overview': {
            'title': _lt('For businesses looking to stay visible and competitive, social media is no longer optional—it’s essential.'),
            'paragraphs': [
                _lt("With over a third of the world’s population active on social platforms, social media has become much more than a place for casual updates. It’s now a dominant space for networking, content discovery, customer engagement, and brand storytelling. Platforms like Facebook, Instagram, LinkedIn, and Twitter have transformed into full-scale marketing ecosystems—offering tools for targeted advertising, real-time interaction, analytics, and campaign management."),
                _lt("What began as informal photo sharing and status updates has matured into a powerful business driver, allowing companies to reach audiences where they spend the most time—on their phones, in their feeds, and ready to engage.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Centralized Campaign Management'),
                'description': _lt('Link and manage profiles from Facebook, LinkedIn, and Twitter—publish, schedule, and attach content to campaigns.'),
                'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image_2.webp'
            },
            {
                'title': _lt('Post Scheduling & Automation'),
                'description': _lt('Create posts, add images, set publishing schedules, and configure push notification details for better timing'),
                'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image_3.webp'
            },
            {
                'title': _lt('Campaign Dashboards'),
                'description': _lt('Organize posts into campaigns and track progress—lead generation, revenue generation, and user engagement—all visualized in a customizable Kanban-style dashboard.'),
                'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image_4.png'
            },
            {
                'title': _lt('Visitor Monitoring'),
                'description': _lt('Track website visitors, page views, number of visits, and lead opportunities. Link visitors to CRM records and initiate follow-up through email or SMS'),
                'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image_5.png'
            },
            {
                'title': _lt('Streamlined Configuration'),
                'description': _lt('Connect your social accounts via developer credentials, enable Demo Mode, and tie in SMS, email, and app channels from a single config interface'),
                'image': '/dekad_website/static/src/img/migrated/apps/social-media-marketing/image_6.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('All-In-One Toolset'),
                    'description': _lt('Host both blog and forum features within the same platform—no need for third-party integrations. Seamlessly manage content and community from a single admin area.')
                },
                {
                    'icon': 'fa-gears',
                    'title': _lt('Smart Lead Generation'),
                    'description': _lt('Adjust layouts, sidebars, and content flow for both blogs and forums to match your brand. Add multiple blogs or forums tailored to audience segments or subjects.')
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('360° Visibility'),
                    'description': _lt('Motivate users with a points system, ranks, badges, and karma-based rewards that encourage meaningful contributions and self-moderation.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Efficient & Cost-Conscious'),
                    'description': _lt('Manage who sees what—set privacy tiers for forums, moderate content flows, and decide what appears on the frontend.')
                }
            ]
        }
    },
    'email-marketing': {
        'slug': 'email-marketing',
        'name': _lt('Email Marketing'),
        'subtitle': _lt('Connect, engage, and convert—with tailored email campaigns built for results'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/email-marketing/cover_bg.webp',
        'overview': {
            'title': _lt('Everything is intuitive, integrated, and efficient—drag, drop, target, and track, without complex setup.'),
            'paragraphs': [
                _lt("Leverage a powerful email marketing suite that lets you design eye-catching campaigns, segment audiences, and measure outcomes—all from one interface. Whether you’re reactivating lost leads or nurturing customers, easily configure emails, schedule sends, and map them to your business goals.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation'
        },
        'key_features': [
            {
                'title': _lt('Drag‑and‑Drop Campaign Builder'),
                'description': _lt('Craft visually compelling emails using a rich template library and intuitive editor—no coding required'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_2.png'
            },
            {
                'title': _lt('Multi‑View Campaign Dashboard'),
                'description': _lt('View your campaigns in List, Kanban, Calendar, or Graph formats. Easily filter, group, and favourite for streamlined tracking'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_3.webp'
            },
            {
                'title': _lt('Audience Segmentation & Lists'),
                'description': _lt('Create and manage mailing lists; import contacts or filter your database. Handle unsubscribes and blacklist entries to stay compliant'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_4.webp'
            },
            {
                'title': _lt('A/B Testing & Advanced Sending Settings'),
                'description': _lt('Test different email variants, compare results, and schedule sends. Configure sender details, preview text, tracking, and attachments'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_5.png'
            },
            {
                'title': _lt('Lost Leads Reactivation'),
                'description': _lt('Automate campaigns to target lost leads with custom filters, optimizing opportunities for re-engagement'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_6.png'
            },
            {
                'title': _lt('Detailed Campaign Analytics'),
                'description': _lt('Monitor opens, clicks, bounces, replies, conversions—and drill down into performance metrics via smart buttons and reports'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_7.webp'
            },
            {
                'title': _lt('Integrated Campaign Workflow'),
                'description': _lt('Align campaigns with CRM leads, events, and more—easily send emails, SMS, or social posts from a unified campaign dashboard'),
                'image': '/dekad_website/static/src/img/migrated/apps/email-marketing/image_8.webp'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-code',
                    'title': _lt('Simple, No-Code Design'),
                    'description': _lt('Make branded emails in minutes using built-in templates and visual tools—no HTML or design skills required.')
                },
                {
                    'icon': 'fa-crosshairs',
                    'title': _lt('Smarter Targeting'),
                    'description': _lt('Segment by behavior, lost leads, or custom criteria; manage unsubscribes cleanly; optimize messaging with A/B tests.')
                },
                {
                    'icon': 'fa-bar-chart-o',
                    'title': _lt('Multi-View Insights'),
                    'description': _lt('Switch between dashboard views for quick overviews or deep dives—list, cards, calendars, or charts.')
                },
                {
                    'icon': 'fa-chain',
                    'title': _lt('Drive Conversions'),
                    'description': _lt('Track full campaign performance—from delivery and opens to link clicks, replies, and eventual sales or leads.')
                },
                {
                    'icon': 'fa-puzzle-piece',
                    'title': _lt('Seamless Integration'),
                    'description': _lt('Connect your mailing lists and lead flows with CRM, events, and marketing automation modules—run campaigns that span channels.')
                }
            ]
        }
    },
    'sms-marketing': {
        'slug': 'sms-marketing',
        'name': _lt('SMS Marketing'),
        'subtitle': _lt('Reach your audience instantly—straight to their mobile devices'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/sms-marketing/cover_bg.webp',
        'overview': {
            'title': _lt('Schedule messages, target precise audiences, and track results—all from one intuitive interface.'),
            'paragraphs': [
                _lt("SMS marketing delivers exceptionally high open rates, making it ideal for event reminders, flash promotions, or important updates. Manage campaigns effortlessly—from contact lists to delivery tracking—without email fatigue.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('SMS Campaign Dashboard'),
                'description': _lt('View your messages in Kanban, List, Calendar, or Graph formats. Monitor statuses like Draft, In Queue, Sending, or Sent.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_2.png'
            },
            {
                'title': _lt('Create & Schedule SMS Mailings'),
                'description': _lt('Design messages with placeholders, choose recipients (mailing lists or filtered contacts), then send now, queue, or schedule for later. Character counters show SMS count in real time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_3.png'
            },
            {
                'title': _lt('Mailing Lists & Blacklists'),
                'description': _lt('Build targeted recipient lists, import/export contacts, and manage unsubscribe requests automatically. Keep communications compliant and respectful.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_4.png'
            },
            {
                'title': _lt('A/B Testing'),
                'description': _lt('Test variations with a sample audience, select winning criteria (clicks, conversions, revenue), and automatically send the best version to the rest.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_5.webp'
            },
            {
                'title': _lt('Link Tracking & Analytics'),
                'description': _lt('Shorten URLs and enable link tracking by default. Access reporting dashboards that show delivery rates, open/click rates, bounces, and campaign-generated leads or revenue.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_6.png'
            },
            {
                'title': _lt('Opt-Out & Compliance Tools'),
                'description': _lt('Include unsubscribe links in messages. Manage blacklisted numbers centrally—either auto or manually added.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_7.png'
            },
            {
                'title': _lt('Contact-Level SMS Sending'),
                'description': _lt('Send one-off messages directly from a contact record in the Contacts app—perfect for quick reminders.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_8.gif'
            },
            {
                'title': _lt('Credits & SMS Types'),
                'description': _lt('Use prepaid credits (no expiration). Support both GSM‑7 (160 chars) and Unicode (70 chars); messages split automatically if needed.'),
                'image': '/dekad_website/static/src/img/migrated/apps/sms-marketing/image_9.png'
            }
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-check-square-o',
                    'title': _lt('Instant Reach with High Engagement'),
                    'description': _lt('SMS open rates (~98%) far outperform email—perfect for urgent updates or time-critical promotions.')
                },
                {
                    'icon': 'fa-thumb-tack',
                    'title': _lt('All-in-One Campaign Control'),
                    'description': _lt('Design, schedule, send, and track—you don’t need separate apps or plugins.')
                },
                {
                    'icon': 'fa-align-left',
                    'title': _lt('Smart A/B Optimization'),
                    'description': _lt('Refine messages based on true performance metrics to drive better results.')
                },
                {
                    'icon': 'fa-random',
                    'title': _lt('Compliance Made Easy'),
                    'description': _lt('Built-in opt-out features, blacklist management, and character tracking ensure clean, legal, and effective messaging.')
                },
                {
                    'icon': '',
                    'title': _lt('Deep Insights & ROI Tracking'),
                    'description': _lt('Link tracking, KPI dashboards, and revenue attribution metrics help measure campaign success accurately.')
                },
                {
                    'icon': '',
                    'title': _lt('Flexible & Cost-Conscious'),
                    'description': _lt('Use pay-as-you-go credits, support core SMS character sets, and send messages directly from CRM or contact forms.')
                }
            ]
        }
    },
    'marketing-automation': {
        'slug': 'marketing-automation',
        'name': _lt('Marketing Automation'),
        'subtitle': _lt('Automate your marketing workflows—without the manual work'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/marketing-automation/cover_bg.webp',
        'overview': {
            'title': _lt('Everything is visual, intuitive, and fully integrated—design flows, test them, launch automatically.'),
            'paragraphs': [
                _lt("Build smart campaigns that trigger actions like emails and SMS based on customer behavior, timing, or conditions. Whether you're welcoming new leads, re-engaging cold contacts, or pushing promotions, this system helps you automate repetitive tasks and reach the right audience at the right moment.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Campaign Templates'),
                'description': _lt('Start quickly using pre-built templates—like Double Opt-In, Welcome Flow, or Hot Lead Alerts—and adapt them to your needs.'),
                'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image_2.webp',
            },
            {
                'title': _lt('Audience Targeting & Filters'),
                'description': _lt('Define precise audiences—such as Leads, Contacts, Event Registrants—then filter your list to match criteria like stage, revenue, or custom fields.'),
                'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image_3.webp',
            },
            {
                'title': _lt('Activity Workflows'),
                'description': _lt('Design visual workflows combining email, SMS, or internal server actions. Set triggers—such as "email opened," "not clicked," or time delays—to guide prospects through engaging sequences.'),
                'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image_4.gif',
            },
            {
                'title': _lt('Testing & Launch'),
                'description': _lt('Run campaigns in test mode using specific contacts to validate flow before sending. Once approved, launch to your full audience. Campaigns can be paused or stopped at any time.'),
                'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image_5.png',
            },
            {
                'title': _lt('Detailed Campaign Analytics'),
                'description': _lt('Track performance metrics like sends, opens, clicks, bounces, and conversions at each step. Real-time charts display success vs. rejection rates per activity.'),
                'image': '/dekad_website/static/src/img/migrated/apps/marketing-automation/image_6.webp',
            },
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-gears',
                    'title': _lt('Effortless Automation'),
                    'description': _lt('Visual building blocks let you automate lead nurturing, follow-ups, and engagement without writing code.'),
                },
                {
                    'icon': 'fa-random',
                    'title': _lt('Pre-built Campaigns Save Time'),
                    'description': _lt('Templates like Double Opt-In or Welcome Flow offer fast paths to deploy best practices instantly.'),
                },
                {
                    'icon': 'fa-group',
                    'title': _lt('Targeted & Flexible'),
                    'description': _lt('Pair audience filters and workflow triggers to create campaigns that adapt to customer actions and attributes.'),
                },
                {
                    'icon': 'fa-paperclip',
                    'title': _lt('Test Before You Launch'),
                    'description': _lt('Validate your campaign with a single contact before launching to your entire list.'),
                },
                {
                    'icon': 'fa-line-chart',
                    'title': _lt('Measurable Results'),
                    'description': _lt('Track every step—deliverability, engagement, conversions—to optimize campaign performance.'),
                },
            ],
        },
    },
    'surveys': {
        'slug': 'surveys',
        'name': _lt('Survey Management'),
        'subtitle': _lt('Gather insights, assess performance, and certify through surveys'),
        'cover_bg': '/dekad_website/static/src/img/migrated/apps/surveys/cover_bg.webp',
        'overview': {
            'title': _lt('Everything is customizable, interactive, and insightful—design forms, analyze responses, and act on results, no coding needed.'),
            'paragraphs': [
                _lt("Create surveys, quizzes, certifications, and live sessions to collect valuable feedback from customers or employees. You can configure passing scores, control access, and present real-time results—all within an intuitive interface.")
            ],
            'image': '/dekad_website/static/src/img/migrated/apps/surveys/image.svg',
            'cta_text': _lt('Book Free Consultation'),
            'cta_url': '/free-consultation',
        },
        'key_features': [
            {
                'title': _lt('Interactive Dashboard'),
                'description': _lt('Access surveys in Kanban, List, or activity views. See key stats at a glance: number of questions, average completion time, participants registered vs. completed, and pass/certification rates for scored surveys.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_2.png',
            },
            {
                'title': _lt('Survey Creation'),
                'description': _lt('Start new surveys instantly from a blank form. Choose types like standard survey, assessment, certification, or live session for real‑time interaction.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_3.png',
            },
            {
                'title': _lt('Dynamic Question Management'),
                'description': _lt('Add sections and questions with various types—multiple-choice, text boxes, numeric, date, matrix. Set mandatory answers, validate entries, and configure conditional display.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_4.png',
            },
            {
                'title': _lt('Scoring & Certification'),
                'description': _lt('Assign scores to answers, set a required pass percentage, and enable certification. Automatically send certificates and award badges when participants pass.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_5.png',
            },
            {
                'title': _lt('Access Control & Attempts'),
                'description': _lt('Choose access modes—anyone with a link or invite only. Require login, limit attempts, and control participant access.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_6.png',
            },
            {
                'title': _lt('Live Session Mode'),
                'description': _lt('Host in-person or virtual sessions where a moderator presents questions live, gathers responses in real time, and reveals results to participants. Add time limits and access codes.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_7.png',
            },
            {
                'title': _lt('Sharing & Testing'),
                'description': _lt('Share survey links via email templates or copy links manually. Test surveys before launch and print forms as needed.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_8.webp',
            },
            {
                'title': _lt('Advanced Analytics'),
                'description': _lt('Review detailed reports with completion stats, pass rates, scores, and individual question analysis. Filter and segment results as needed.'),
                'image': '/dekad_website/static/src/img/migrated/apps/surveys/image_9.webp',
            },
        ],
        'why_choose_us': {
            'title': _lt('Everything you need'),
            'features': [
                {
                    'icon': 'fa-align-center',
                    'title': _lt('Versatile Use Cases'),
                    'description': _lt('Use it for feedback collection, knowledge assessments, certification programs, or live presentations—all within one tool.'),
                },
                {
                    'icon': 'fa-sliders',
                    'title': _lt('Engaging & Insightful'),
                    'description': _lt('With certifications, badges, timed live interactions, and conditional logic, engagement and understanding increase dramatically.'),
                },
                {
                    'icon': 'fa-toggle-on',
                    'title': _lt('Real-Time Feedback'),
                    'description': _lt('Live sessions provide instant visualization of responses—perfect for interactive workshops or group training.'),
                },
                {
                    'icon': 'fa-external-link-square',
                    'title': _lt('Data-Driven Improvements'),
                    'description': _lt('Dashboard analytics and question-level insights help you refine surveys, courses, and sessions over time.'),
                },
                {
                    'icon': 'fa-lock',
                    'title': _lt('Controlled & Secure'),
                    'description': _lt('Manage who participates, how many times they can take the survey, and ensure only qualified participants can complete it.'),
                },
            ],
        },
    },
}