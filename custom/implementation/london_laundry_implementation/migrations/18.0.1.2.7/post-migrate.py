def migrate(cr, version):
    # بيانات طرق التوصيل noupdate: "Home Delivery" الموجودة صارت بأجرة توصيل
    cr.execute("""
        UPDATE london_delivery_method m SET laundry_with_charge = TRUE
          FROM ir_model_data d
         WHERE d.model = 'london.delivery.method' AND d.res_id = m.id
           AND d.module = 'london_laundry_implementation' AND d.name = 'delivery_method_home'
    """)
    # منتج التوصيل انخلق بعد ما انضاف الحقل على نقاط البيع: منربطه هلق
    cr.execute("""
        UPDATE pos_config c SET laundry_delivery_product_id = d.res_id
          FROM ir_model_data d
         WHERE d.module = 'london_laundry_implementation' AND d.name = 'product_laundry_delivery'
           AND c.laundry_delivery_product_id IS NULL
    """)
